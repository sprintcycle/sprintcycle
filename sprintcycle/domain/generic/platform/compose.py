"""Platform compose composition for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ...infrastructure.integrations.autogpt.compose import ComposeSpec, build_default_compose_spec
from .spec import PlatformSpec, build_platform_spec


@dataclass
class PlatformComposeBundle:
    platform: PlatformSpec
    compose: ComposeSpec

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.to_dict(),
            "compose": self.compose.to_dict(),
        }


def build_platform_compose_bundle(project_name: str = "sprintcycle") -> PlatformComposeBundle:
    platform = build_platform_spec(project_name)
    compose = build_default_compose_spec(project_name)
    return PlatformComposeBundle(platform=platform, compose=compose)


__all__ = ["PlatformComposeBundle", "build_platform_compose_bundle"]
