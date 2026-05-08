"""真实编码引擎适配层。"""

from __future__ import annotations

import asyncio
import json
import os
import random
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib import error, request


@dataclass
class EngineExecutionResult:
    success: bool
    output: str = ""
    error: str = ""
    error_code: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    command: List[str] = field(default_factory=list)
    exit_code: Optional[int] = None
    timed_out: bool = False
    request_id: str = ""
    trace_id: str = ""


@dataclass
class EngineAdapterConfig:
    timeout_seconds: int = 900
    cwd: str = "."
    max_output_chars: int = 20000
    max_retries: int = 2
    retry_backoff_seconds: float = 0.75


class BaseEngineAdapter:
    name: str = "base"

    def __init__(self, config: Optional[EngineAdapterConfig] = None) -> None:
        self.config = config or EngineAdapterConfig()

    async def execute(self, prompt: str, context: Dict[str, Any]) -> EngineExecutionResult:
        raise NotImplementedError

    def _base_metadata(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "engine": self.name,
            "cwd": str(context.get("project_path") or self.config.cwd or "."),
            "sprint_name": context.get("sprint_name", ""),
            "release_plan_id": context.get("release_plan_id", ""),
            "prompt_chars": len(prompt),
            "timeout_seconds": self.config.timeout_seconds,
        }

    def _mk_ids(self) -> tuple[str, str]:
        return str(uuid.uuid4()), str(uuid.uuid4())

    def _http_post_json(self, url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout_seconds: int) -> tuple[int, str, str]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=timeout_seconds) as resp:
                out = resp.read().decode("utf-8", errors="ignore")
                return resp.status, out, ""
        except error.HTTPError as e:
            status = getattr(e, "code", 500)
            err = ""
            try:
                err = e.read().decode("utf-8", errors="ignore")
            except Exception:
                err = str(e)
            return status, "", err
        except TimeoutError as e:
            return 408, "", str(e)
        except Exception as e:
            return 599, "", str(e)

    async def _post_with_retry(self, *args: Any, **kwargs: Any) -> tuple[int, str, str, int]:
        attempt = 0
        while True:
            status, out, err = await asyncio.to_thread(self._http_post_json, *args, **kwargs)
            if status not in (429, 408, 599):
                return status, out, err, attempt
            attempt += 1
            if attempt > self.config.max_retries:
                return status, out, err, attempt
            await asyncio.sleep(self.config.retry_backoff_seconds * (2 ** (attempt - 1)) + random.random() * 0.1)

    def _success(self, *, output: str, metadata: Dict[str, Any], request_id: str, trace_id: str) -> EngineExecutionResult:
        return EngineExecutionResult(success=True, output=output[: self.config.max_output_chars], error="", error_code="ok", metadata=metadata, request_id=request_id, trace_id=trace_id)

    def _failure(self, *, error_message: str, error_code: str, metadata: Dict[str, Any], request_id: str, trace_id: str) -> EngineExecutionResult:
        return EngineExecutionResult(success=False, output="", error=error_message[: self.config.max_output_chars], error_code=error_code, metadata=metadata, request_id=request_id, trace_id=trace_id)


class CursorEngineAdapter(BaseEngineAdapter):
    name = "cursor"

    def _sdk_client(self) -> Optional[Any]:
        try:
            from cursor import Cursor
        except Exception:
            return None
        api_key = os.environ.get("CURSOR_API_KEY", "")
        api_base = os.environ.get("CURSOR_API_BASE", "") or None
        if not api_key:
            return None
        kwargs: Dict[str, Any] = {"api_key": api_key}
        if api_base:
            kwargs["base_url"] = api_base
        return Cursor(**kwargs)

    async def execute(self, prompt: str, context: Dict[str, Any]) -> EngineExecutionResult:
        request_id, trace_id = self._mk_ids()
        api_base = os.environ.get("CURSOR_API_BASE", "").rstrip("/")
        api_key = os.environ.get("CURSOR_API_KEY", "")
        metadata = {**self._base_metadata(prompt, context), "adapter": "cursor", "transport": "api", "api_base": api_base, "request_id": request_id, "trace_id": trace_id}
        client = self._sdk_client()
        if client is not None:
            try:
                def _call() -> str:
                    resp = client.execute(prompt=prompt, context=context)
                    return getattr(resp, "text", str(resp))

                text = await asyncio.wait_for(asyncio.to_thread(_call), timeout=self.config.timeout_seconds)
                metadata["transport"] = "sdk"
                metadata["sdk"] = "cursor"
                return self._success(output=text, metadata=metadata, request_id=request_id, trace_id=trace_id)
            except asyncio.TimeoutError:
                return self._failure(error_message="cursor sdk timeout", error_code="timeout", metadata=metadata, request_id=request_id, trace_id=trace_id)
            except Exception as e:
                metadata["sdk_fallback_reason"] = str(e)

        if not api_base or not api_key:
            return self._failure(error_message="cursor api configuration missing", error_code="config_missing", metadata={**metadata, "api_key_present": bool(api_key)}, request_id=request_id, trace_id=trace_id)
        payload = {"prompt": prompt, "context": context, "request_id": request_id, "trace_id": trace_id}
        status, out, err, attempts = await self._post_with_retry(f"{api_base}/v1/execute", payload, {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, self.config.timeout_seconds)
        metadata["attempts"] = attempts
        if 200 <= status < 300:
            return self._success(output=out, metadata=metadata, request_id=request_id, trace_id=trace_id)
        code = "auth_failed" if status in (401, 403) else "timeout" if status == 408 else "rate_limited" if status == 429 else "api_error"
        return self._failure(error_message=err or out or f"cursor api error {status}", error_code=code, metadata=metadata, request_id=request_id, trace_id=trace_id)


class ClaudeEngineAdapter(BaseEngineAdapter):
    name = "claude"

    def _sdk_client(self) -> Optional[Any]:
        try:
            from anthropic import Anthropic
        except Exception:
            return None
        api_key = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("CLAUDE_API_KEY", "")
        if not api_key:
            return None
        api_base = os.environ.get("ANTHROPIC_BASE_URL", "") or os.environ.get("CLAUDE_API_BASE", "") or None
        kwargs: Dict[str, Any] = {"api_key": api_key}
        if api_base:
            kwargs["base_url"] = api_base
        return Anthropic(**kwargs)

    async def execute(self, prompt: str, context: Dict[str, Any]) -> EngineExecutionResult:
        request_id, trace_id = self._mk_ids()
        api_key = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("CLAUDE_API_KEY", "")
        api_base = (os.environ.get("ANTHROPIC_BASE_URL", "") or os.environ.get("CLAUDE_API_BASE", "") or "https://api.anthropic.com").rstrip("/")
        metadata = {**self._base_metadata(prompt, context), "adapter": "claude", "transport": "api", "api_base": api_base, "request_id": request_id, "trace_id": trace_id}
        client = self._sdk_client()
        if client is not None:
            try:
                def _call() -> str:
                    msg = client.messages.create(
                        model=os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-latest"),
                        max_tokens=int(os.environ.get("CLAUDE_MAX_TOKENS", "4096")),
                        messages=[{"role": "user", "content": prompt}],
                    )
                    parts = getattr(msg, "content", []) or []
                    return "\n".join(getattr(part, "text", "") for part in parts if getattr(part, "type", "") == "text")

                text = await asyncio.wait_for(asyncio.to_thread(_call), timeout=self.config.timeout_seconds)
                metadata["transport"] = "sdk"
                metadata["sdk"] = "anthropic"
                return self._success(output=text, metadata=metadata, request_id=request_id, trace_id=trace_id)
            except asyncio.TimeoutError:
                return self._failure(error_message="claude sdk timeout", error_code="timeout", metadata=metadata, request_id=request_id, trace_id=trace_id)
            except Exception as e:
                metadata["sdk_fallback_reason"] = str(e)

        if not api_key:
            return self._failure(error_message="claude api key missing", error_code="config_missing", metadata={**metadata, "api_key_present": False}, request_id=request_id, trace_id=trace_id)
        payload = {"model": os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-latest"), "max_tokens": int(os.environ.get("CLAUDE_MAX_TOKENS", "4096")), "messages": [{"role": "user", "content": prompt}]}
        status, out, err, attempts = await self._post_with_retry(f"{api_base}/v1/messages", payload, {"x-api-key": api_key, "anthropic-version": os.environ.get("ANTHROPIC_VERSION", "2023-06-01"), "content-type": "application/json"}, self.config.timeout_seconds)
        metadata["attempts"] = attempts
        if 200 <= status < 300:
            try:
                data = json.loads(out)
                content = data.get("content", [])
                text = "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
            except Exception:
                text = out
            return self._success(output=text, metadata=metadata, request_id=request_id, trace_id=trace_id)
        code = "auth_failed" if status in (401, 403) else "timeout" if status == 408 else "rate_limited" if status == 429 else "api_error"
        return self._failure(error_message=err or out or f"claude api error {status}", error_code=code, metadata=metadata, request_id=request_id, trace_id=trace_id)


class TraeEngineAdapter(BaseEngineAdapter):
    name = "trae"

    def _sdk_client(self) -> Optional[Any]:
        try:
            from trae import Trae
        except Exception:
            return None
        api_key = os.environ.get("TRAE_API_KEY", "")
        api_base = os.environ.get("TRAE_API_BASE", "") or None
        if not api_key:
            return None
        kwargs: Dict[str, Any] = {"api_key": api_key}
        if api_base:
            kwargs["base_url"] = api_base
        return Trae(**kwargs)

    async def execute(self, prompt: str, context: Dict[str, Any]) -> EngineExecutionResult:
        request_id, trace_id = self._mk_ids()
        api_base = os.environ.get("TRAE_API_BASE", "").rstrip("/")
        api_key = os.environ.get("TRAE_API_KEY", "")
        metadata = {**self._base_metadata(prompt, context), "adapter": "trae", "transport": "api", "api_base": api_base, "request_id": request_id, "trace_id": trace_id}
        client = self._sdk_client()
        if client is not None:
            try:
                def _call() -> str:
                    resp = client.generate(prompt=prompt, context=context)
                    return getattr(resp, "text", str(resp))

                text = await asyncio.wait_for(asyncio.to_thread(_call), timeout=self.config.timeout_seconds)
                metadata["transport"] = "sdk"
                metadata["sdk"] = "trae"
                return self._success(output=text, metadata=metadata, request_id=request_id, trace_id=trace_id)
            except asyncio.TimeoutError:
                return self._failure(error_message="trae sdk timeout", error_code="timeout", metadata=metadata, request_id=request_id, trace_id=trace_id)
            except Exception as e:
                metadata["sdk_fallback_reason"] = str(e)

        if not api_base or not api_key:
            return self._failure(error_message="trae api configuration missing", error_code="config_missing", metadata={**metadata, "api_key_present": bool(api_key)}, request_id=request_id, trace_id=trace_id)
        payload = {"prompt": prompt, "context": context, "request_id": request_id, "trace_id": trace_id}
        status, out, err, attempts = await self._post_with_retry(f"{api_base}/v1/generate", payload, {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, self.config.timeout_seconds)
        metadata["attempts"] = attempts
        if 200 <= status < 300:
            return self._success(output=out, metadata=metadata, request_id=request_id, trace_id=trace_id)
        code = "auth_failed" if status in (401, 403) else "timeout" if status == 408 else "rate_limited" if status == 429 else "api_error"
        return self._failure(error_message=err or out or f"trae api error {status}", error_code=code, metadata=metadata, request_id=request_id, trace_id=trace_id)


def resolve_engine_adapter(name: str, config: Optional[EngineAdapterConfig] = None) -> BaseEngineAdapter:
    n = (name or "cursor").lower()
    if n == "claude":
        return ClaudeEngineAdapter(config)
    if n == "trae":
        return TraeEngineAdapter(config)
    return CursorEngineAdapter(config)


__all__ = ["BaseEngineAdapter", "CursorEngineAdapter", "ClaudeEngineAdapter", "TraeEngineAdapter", "resolve_engine_adapter", "EngineExecutionResult", "EngineAdapterConfig"]
