"""
Cursor ACP Client - Python 客户端
通过 ACP 协议调用 Cursor CLI 的完整能力
"""
import subprocess
import json
import threading
import queue
from typing import Optional, Callable, Dict, Any


class CursorACPClient:
    """
    Cursor Agent Client Protocol 客户端
    
    使用方式:
        client = CursorACPClient()
        client.start()
        
        # 创建会话
        session = await client.new_session(prompt="实现用户登录接口")
        
        # 发送消息
        response = await client.send_message("添加 JWT 认证")
    """
    
    def __init__(self, agent_path: str = "agent"):
        self.agent_path = agent_path
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.pending = {}  # 等待响应的请求
        self.message_queue = queue.Queue()
        self.reader_thread: Optional[threading.Thread] = None
        
    def start(self):
        """启动 Cursor Agent"""
        self.process = subprocess.Popen(
            [self.agent_path, "acp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 启动读取线程
        self.reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.reader_thread.start()
        
    def _read_loop(self):
        """持续读取 stdout"""
        for line in self.process.stdout:
            try:
                msg = json.loads(line.strip())
                self._handle_message(msg)
            except json.JSONDecodeError:
                continue
                
    def _handle_message(self, msg: dict):
        """处理收到的消息"""
        msg_id = msg.get("id")
        
        # 响应消息
        if msg_id and (msg.get("result") or msg.get("error")):
            if msg_id in self.pending:
                self.pending[msg_id].put(msg)
            return
            
        # 通知消息
        method = msg.get("method")
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
        self.process.stdin.write(json.dumps(msg) + "\n")
        self.process.stdin.flush()
        return self.request_id
        
    def _wait_response(self, msg_id: int, timeout: float = 60) -> dict:
        """等待响应"""
        if msg_id not in self.pending:
            self.pending[msg_id] = queue.Queue()
            
        try:
            return self.pending[msg_id].get(timeout=timeout)
        except queue.Empty:
            return {"error": {"message": "timeout"}}
            
    # ========== 初始化 ==========
    
    def initialize(self) -> dict:
        """初始化 ACP 连接"""
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
        return self._wait_response(msg_id)
        
    # ========== 会话管理 ==========
    
    def new_session(self, prompt: str, mode: str = "agent", cwd: str = None) -> dict:
        """
        创建新会话
        
        Args:
            prompt: 初始提示词
            mode: agent / plan / ask
            cwd: 工作目录
        """
        params = {
            "prompt": prompt,
            "mode": mode
        }
        if cwd:
            params["cwd"] = cwd
            
        msg_id = self._send("session/new", params)
        return self._wait_response(msg_id, timeout=300)  # 5分钟超时
        
    def load_session(self, session_id: str) -> dict:
        """加载已有会话"""
        msg_id = self._send("session/load", {"sessionId": session_id})
        return self._wait_response(msg_id)
        
    # ========== 消息发送 ==========
    
    def send_message(self, session_id: str, message: str) -> dict:
        """发送消息到会话"""
        msg_id = self._send("session/message", {
            "sessionId": session_id,
            "message": message
        })
        return self._wait_response(msg_id, timeout=300)
        
    # ========== 权限处理 ==========
    
    def allow_permission(self, permission_id: str, always: bool = False):
        """允许权限请求"""
        option = "allow-always" if always else "allow-once"
        self._send("session/respond_permission", {
            "permissionId": permission_id,
            "outcome": {"outcome": "selected", "optionId": option}
        })
        
    def reject_permission(self, permission_id: str):
        """拒绝权限请求"""
        self._send("session/respond_permission", {
            "permissionId": permission_id,
            "outcome": {"outcome": "selected", "optionId": "reject-once"}
        })
        
    # ========== 流式消息 ==========
    
    def get_updates(self, callback: Callable[[dict], None]):
        """
        获取会话更新（流式）
        
        使用方式:
            def on_update(msg):
                if msg.get("method") == "session/update":
                    content = msg["params"]["update"].get("content", {})
                    print(content.get("text", ""))
                    
            client.get_updates(on_update)
        """
        while True:
            try:
                msg = self.message_queue.get(timeout=1)
                callback(msg)
            except queue.Empty:
                continue
                
    def stop(self):
        """停止客户端"""
        if self.process:
            self.process.terminate()
            self.process.wait()


# ========== 便捷函数 ==========

def execute_with_cursor(
    task: str,
    project_path: str = ".",
    mode: str = "agent",
    auto_approve: bool = True
) -> str:
    """
    使用 Cursor 执行任务（简化版）
    
    Args:
        task: 任务描述
        project_path: 项目路径
        mode: agent / plan / ask
        auto_approve: 是否自动批准权限请求
        
    Returns:
        执行结果
    """
    import os
    
    client = CursorACPClient()
    client.start()
    
    try:
        # 初始化
        init_result = client.initialize()
        if init_result.get("error"):
            return f"初始化失败: {init_result['error']}"
            
        # 创建会话
        session_result = client.new_session(
            prompt=task,
            mode=mode,
            cwd=os.path.abspath(project_path)
        )
        
        if session_result.get("error"):
            return f"会话创建失败: {session_result['error']}"
            
        # 收集响应
        result_text = []
        
        def on_update(msg):
            if msg.get("method") == "session/update":
                update = msg.get("params", {}).get("update", {})
                if update.get("sessionUpdate") == "agent_message_chunk":
                    text = update.get("content", {}).get("text", "")
                    result_text.append(text)
                    
                # 自动批准权限
                elif msg.get("method") == "session/request_permission" and auto_approve:
                    permission_id = msg.get("id")
                    client.allow_permission(permission_id, always=auto_approve)
                    
        # 运行直到完成
        client.get_updates(on_update)
        
        return "".join(result_text)
        
    finally:
        client.stop()


# ========== CLI 入口 ==========

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cursor ACP Client")
    parser.add_argument("task", help="任务描述")
    parser.add_argument("--project", "-p", default=".", help="项目路径")
    parser.add_argument("--mode", "-m", default="agent", choices=["agent", "plan", "ask"])
    
    args = parser.parse_args()
    
    result = execute_with_cursor(
        task=args.task,
        project_path=args.project,
        mode=args.mode
    )
    
    print(result)
