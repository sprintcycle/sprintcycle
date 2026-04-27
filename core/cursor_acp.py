"""
Cursor ACP Client v1.0
SprintCycle 执行层 - 通过 ACP 协议调用 Cursor
"""
import subprocess
import json
import threading
import queue
import os
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class SessionMode(Enum):
    AGENT = "agent"    # 完整能力
    PLAN = "plan"      # 规划模式
    ASK = "ask"        # 问答模式


@dataclass
class ACPResult:
    success: bool
    output: str
    files_changed: List[str]
    error: Optional[str] = None
    session_id: Optional[str] = None


class CursorACPClient:
    """
    Cursor ACP 客户端
    
    通过 JSON-RPC 协议与 Cursor Agent 通信
    支持流式输出、自动权限批准、会话管理
    """
    
    def __init__(self, agent_path: str = "agent"):
        self.agent_path = agent_path
        self.process: Optional[subprocess.Popen] = None
        self.reader_thread: Optional[threading.Thread] = None
        self.message_queue: queue.Queue = queue.Queue()
        self.response_queue: queue.Queue = queue.Queue()
        self.request_id = 0
        self.session_id: Optional[str] = None
        self._running = False
        
    def start(self) -> bool:
        """启动 Cursor Agent ACP 服务"""
        try:
            self.process = subprocess.Popen(
                [self.agent_path, "acp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            self._running = True
            
            # 启动读取线程
            self.reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.reader_thread.start()
            
            # 初始化协议
            return self._initialize()
        except FileNotFoundError:
            return False
        except Exception:
            return False
            
    def _read_loop(self):
        """持续读取 stdout"""
        while self._running and self.process:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
                msg = json.loads(line.strip())
                self._handle_message(msg)
            except json.JSONDecodeError:
                continue
            except Exception:
                break
                
    def _handle_message(self, msg: dict):
        """处理消息"""
        msg_id = msg.get("id")
        method = msg.get("method")
        
        # 响应消息
        if msg_id is not None and (msg.get("result") or msg.get("error")):
            self.response_queue.put(msg)
            return
            
        # 通知消息
        if method:
            self.message_queue.put(msg)
            
    def _send(self, method: str, params: dict = None) -> int:
        """发送 JSON-RPC 请求"""
        self.request_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        if self.process and self.process.stdin:
            self.process.stdin.write(json.dumps(msg) + "\n")
            self.process.stdin.flush()
            
        return self.request_id
        
    def _wait_response(self, msg_id: int, timeout: float = 60) -> dict:
        """等待响应"""
        start = time.time() if 'time' in dir() else 0
        while True:
            try:
                msg = self.response_queue.get(timeout=1)
                if msg.get("id") == msg_id:
                    return msg
                else:
                    self.response_queue.put(msg)  # 放回
            except queue.Empty:
                continue
            if timeout and (time.time() - start > timeout if 'time' in dir() else False):
                break
        return {"error": {"message": "timeout"}}
        
    def _initialize(self) -> bool:
        """初始化 ACP 连接"""
        import time
        msg_id = self._send("initialize", {
            "protocolVersion": 1,
            "clientCapabilities": {
                "fs": {"readTextFile": True, "writeTextFile": True},
                "terminal": True
            },
            "clientInfo": {
                "name": "sprintcycle-cursor-client",
                "version": "1.0.0"
            }
        })
        
        start = time.time()
        while time.time() - start < 10:
            try:
                msg = self.response_queue.get(timeout=1)
                if msg.get("id") == msg_id:
                    return not msg.get("error")
            except queue.Empty:
                continue
        return False
        
    def create_session(
        self,
        prompt: str,
        mode: SessionMode = SessionMode.AGENT,
        cwd: str = None
    ) -> ACPResult:
        """
        创建新会话
        
        Args:
            prompt: 任务描述
            mode: agent / plan / ask
            cwd: 工作目录
        """
        params = {
            "prompt": prompt,
            "mode": mode.value
        }
        if cwd:
            params["cwd"] = os.path.abspath(cwd)
            
        msg_id = self._send("session/new", params)
        
        # 等待响应并收集输出
        return self._collect_session_output(msg_id)
        
    def _collect_session_output(self, msg_id: int, timeout: float = 300) -> ACPResult:
        """收集会话输出"""
        import time
        
        output_parts = []
        files_changed = []
        session_id = None
        error = None
        
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                # 检查响应
                msg = self.response_queue.get(timeout=0.5)
                if msg.get("id") == msg_id:
                    result = msg.get("result", {})
                    session_id = result.get("sessionId")
                continue
            except queue.Empty:
                pass
                
            # 检查通知
            try:
                msg = self.message_queue.get(timeout=0.5)
                method = msg.get("method")
                
                if method == "session/update":
                    update = msg.get("params", {}).get("update", {})
                    update_type = update.get("sessionUpdate")
                    
                    if update_type == "agent_message_chunk":
                        text = update.get("content", {}).get("text", "")
                        output_parts.append(text)
                        
                    elif update_type == "tool_result":
                        # 工具执行结果
                        tool_name = update.get("toolName", "")
                        if tool_name in ["write_to_file", "edit_file"]:
                            file_path = update.get("result", {}).get("path", "")
                            if file_path:
                                files_changed.append(file_path)
                                
                elif method == "session/request_permission":
                    # 自动批准权限
                    permission_id = msg.get("id")
                    self._approve_permission(permission_id)
                    
                elif method == "session/completed":
                    # 会话完成
                    break
                    
            except queue.Empty:
                continue
                
        return ACPResult(
            success=True,
            output="".join(output_parts),
            files_changed=files_changed,
            session_id=session_id,
            error=error
        )
        
    def _approve_permission(self, permission_id: int, always: bool = True):
        """批准权限请求"""
        option = "allow-always" if always else "allow-once"
        self._send("session/respond_permission", {
            "permissionId": permission_id,
            "outcome": {"outcome": "selected", "optionId": option}
        })
        
    def continue_session(self, message: str) -> ACPResult:
        """继续会话"""
        if not self.session_id:
            return ACPResult(
                success=False,
                output="",
                files_changed=[],
                error="没有活动会话"
            )
            
        msg_id = self._send("session/message", {
            "sessionId": self.session_id,
            "message": message
        })
        
        return self._collect_session_output(msg_id)
        
    def stop(self):
        """停止客户端"""
        self._running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()


# ========== 便捷函数 ==========

def execute_with_cursor(
    task: str,
    project_path: str = ".",
    mode: str = "agent",
    auto_approve: bool = True
) -> ACPResult:
    """
    使用 Cursor 执行任务
    
    Args:
        task: 任务描述
        project_path: 项目路径
        mode: agent / plan / ask
        auto_approve: 自动批准权限
        
    Returns:
        ACPResult
    """
    client = CursorACPClient()
    
    if not client.start():
        return ACPResult(
            success=False,
            output="",
            files_changed=[],
            error="Cursor CLI 未安装或未登录"
        )
        
    try:
        mode_enum = SessionMode(mode)
    except ValueError:
        mode_enum = SessionMode.AGENT
        
    result = client.create_session(
        prompt=task,
        mode=mode_enum,
        cwd=project_path
    )
    
    client.stop()
    return result


def check_cursor_available() -> tuple:
    """检查 Cursor CLI 是否可用"""
    result = subprocess.run(
        ["which", "agent"],
        capture_output=True
    )
    
    if result.returncode != 0:
        return False, "Cursor CLI 未安装。安装命令: curl https://cursor.com/install | bash"
        
    # 检查是否登录
    result = subprocess.run(
        ["agent", "--version"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return True, f"Cursor CLI 可用: {result.stdout.strip()}"
    else:
        return False, "Cursor CLI 未登录。请运行: agent login"
