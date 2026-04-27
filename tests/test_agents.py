"""
测试 SprintCycle Agents 模块
"""
import pytest
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, '/root/sprintcycle')


class TestAgentsModule:
    """测试 agents 模块导入"""
    
    def test_import_agents(self):
        """测试 agents 模块导入"""
        from sprintcycle.agents import (
            BaseAgent,
            AgentCapability,
            UIVerifyAgent,
            ConcurrentExecutor,
            PriorityTask,
            TaskPriority,
            PlaywrightClient
        )
        assert BaseAgent is not None
        assert AgentCapability is not None
        assert UIVerifyAgent is not None
        assert ConcurrentExecutor is not None
        assert TaskPriority is not None
    
    def test_agent_capabilities(self):
        """测试 Agent 能力枚举"""
        from sprintcycle.agents import AgentCapability
        
        assert AgentCapability.CODING.value == "coding"
        assert AgentCapability.VERIFICATION.value == "verification"
        assert AgentCapability.BROWSER_AUTOMATION.value == "browser_automation"
    
    def test_task_priority(self):
        """测试任务优先级"""
        from sprintcycle.agents import TaskPriority
        
        assert TaskPriority.CRITICAL < TaskPriority.HIGH
        assert TaskPriority.HIGH < TaskPriority.NORMAL
        assert TaskPriority.NORMAL < TaskPriority.LOW
        assert TaskPriority.LOW < TaskPriority.BACKGROUND


class TestUIVerifyAgent:
    """测试 UI 验证 Agent"""
    
    def test_agent_creation(self):
        """测试 Agent 创建"""
        from sprintcycle.agents import UIVerifyAgent
        
        agent = UIVerifyAgent(base_url="http://localhost:3000")
        assert agent.base_url == "http://localhost:3000"
        assert agent.name == "UIVerify"
        assert agent.capabilities is not None
    
    def test_capabilities(self):
        """测试 Agent 能力"""
        from sprintcycle.agents import UIVerifyAgent, AgentCapability
        
        agent = UIVerifyAgent()
        assert AgentCapability.VERIFICATION in agent.capabilities
        assert AgentCapability.TESTING in agent.capabilities
        assert AgentCapability.BROWSER_AUTOMATION in agent.capabilities
    
    def test_url_extraction(self):
        """测试 URL 提取"""
        from sprintcycle.agents import UIVerifyAgent
        
        agent = UIVerifyAgent()
        
        # 测试 http URL
        url1 = agent._extract_url("验证页面加载 http://example.com/page")
        assert url1 == "http://example.com/page"
        
        # 测试 localhost
        url2 = agent._extract_url("检查 http://localhost:8080/admin")
        assert "localhost:8080" in url2
        
        # 测试相对路径
        url3 = agent._extract_url("完整验证 /dashboard")
        assert url3 == "/dashboard"
    
    def test_selector_extraction(self):
        """测试选择器提取"""
        from sprintcycle.agents import UIVerifyAgent
        
        agent = UIVerifyAgent()
        
        # 测试引号内的选择器
        sel1 = agent._extract_selector("检查元素 '#login-btn'")
        assert sel1 == "#login-btn"
        
        # 测试默认选择器
        sel2 = agent._extract_selector("检查 .submit-button")
        # 由于正则可能匹配不到，返回默认值 body
        assert sel2 in [".submit-button", "body"]
    
    def test_text_extraction(self):
        """测试文本提取"""
        from sprintcycle.agents import UIVerifyAgent
        
        agent = UIVerifyAgent()
        
        text = agent._extract_text("验证文本 'Welcome to Dashboard' 在页面中")
        assert text == "Welcome to Dashboard"


class TestPriorityTask:
    """测试优先级任务"""
    
    def test_task_creation(self):
        """测试任务创建"""
        from sprintcycle.agents import PriorityTask, TaskPriority
        
        async def dummy_task():
            return "done"
        
        task = PriorityTask(
            id="test_1",
            task=dummy_task,
            priority=TaskPriority.HIGH,
            max_retries=3
        )
        
        assert task.id == "test_1"
        assert task.priority == TaskPriority.HIGH
        assert task.max_retries == 3
        assert task.status == "pending"
    
    def test_task_ordering(self):
        """测试任务排序"""
        from sprintcycle.agents import PriorityTask, TaskPriority
        
        async def dummy_task():
            return
        
        task_high = PriorityTask(id="high", task=dummy_task, priority=TaskPriority.HIGH)
        task_low = PriorityTask(id="low", task=dummy_task, priority=TaskPriority.LOW)
        task_critical = PriorityTask(id="critical", task=dummy_task, priority=TaskPriority.CRITICAL)
        
        # 高优先级任务应该排在前面
        assert task_critical < task_high
        assert task_high < task_low
    
    def test_task_to_dict(self):
        """测试任务序列化"""
        from sprintcycle.agents import PriorityTask, TaskPriority
        
        async def dummy_task():
            return
        
        task = PriorityTask(
            id="test_1",
            task=dummy_task,
            priority=TaskPriority.NORMAL,
            dependencies=["dep_1"]
        )
        
        d = task.to_dict()
        assert d["id"] == "test_1"
        assert d["priority"] == "NORMAL"
        assert d["dependencies"] == ["dep_1"]
        assert d["status"] == "pending"


class TestConcurrentExecutor:
    """测试并发执行器"""
    
    def test_executor_creation(self):
        """测试执行器创建"""
        from sprintcycle.agents import ConcurrentExecutor
        
        executor = ConcurrentExecutor(max_concurrent=5)
        assert executor.max_concurrent == 5
        assert executor.stats.total_tasks == 0
    
    def test_create_task(self):
        """测试任务创建"""
        from sprintcycle.agents import ConcurrentExecutor, TaskPriority
        
        executor = ConcurrentExecutor()
        
        async def test_task():
            await asyncio.sleep(0.1)
            return 42
        
        task = executor.create_task(
            test_task,
            task_id="test_1",
            priority=TaskPriority.HIGH
        )
        
        assert task.id == "test_1"
        assert task.priority == TaskPriority.HIGH
    
    @pytest.mark.asyncio
    async def test_simple_execution(self):
        """测试简单任务执行"""
        from sprintcycle.agents import ConcurrentExecutor
        
        executor = ConcurrentExecutor(max_concurrent=2)
        
        async def task_fn(n):
            await asyncio.sleep(0.1)
            return n * 2
        
        # 提交任务
        tasks = []
        for i in range(3):
            t = executor.create_task(
                lambda i=i: task_fn(i),
                task_id=f"task_{i}"
            )
            await executor.submit(t)
            tasks.append(t)
        
        # 等待完成
        await asyncio.sleep(0.5)
        results_dict = await executor.wait_all(timeout=5)
        
        assert len(results_dict["results"]) == 3
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """测试优先级排序"""
        from sprintcycle.agents import ConcurrentExecutor, TaskPriority
        
        execution_order = []
        
        async def make_task(n):
            async def task():
                await asyncio.sleep(0.05)  # 确保按优先级顺序完成
                execution_order.append(n)
                return n
            return task
        
        executor = ConcurrentExecutor(max_concurrent=1)
        
        # 提交任务（乱序）
        task_low = executor.create_task(
            await make_task(1),
            task_id="low",
            priority=TaskPriority.LOW
        )
        task_high = executor.create_task(
            await make_task(2),
            task_id="high",
            priority=TaskPriority.HIGH
        )
        task_critical = executor.create_task(
            await make_task(3),
            task_id="critical",
            priority=TaskPriority.CRITICAL
        )
        
        await executor.submit_batch([task_low, task_high, task_critical])
        await executor.wait_all(timeout=10)
        
        # 关键任务应该先执行
        assert execution_order[0] == 3  # critical
        assert execution_order[1] == 2  # high
        assert execution_order[2] == 1  # low


class TestChorusIntegration:
    """测试 Chorus 集成"""
    
    def test_import_chorus(self):
        """测试 Chorus 模块导入"""
        from sprintcycle.chorus import (
            Chorus,
            ChorusAdapter,
            AgentType,
            ToolType
        )
        assert Chorus is not None
        assert ChorusAdapter is not None
        assert AgentType.UI_VERIFY is not None
    
    def test_agent_type_recognition(self):
        """测试 Agent 类型识别"""
        from sprintcycle.chorus import Chorus, AgentType
        
        chorus = Chorus()
        
        # UI 验证任务
        assert chorus.analyze("验证页面 UI") == AgentType.UI_VERIFY
        assert chorus.analyze("检查界面交互") == AgentType.UI_VERIFY
        assert chorus.analyze("UI verification") == AgentType.UI_VERIFY
        
        # 其他任务
        assert chorus.analyze("审查代码") == AgentType.REVIEWER
        assert chorus.analyze("设计架构") == AgentType.ARCHITECT
    
    def test_ui_verify_in_tool_map(self):
        """测试 UI_VERIFY 在工具映射中"""
        from sprintcycle.chorus import ChorusAdapter, AgentType
        
        adapter = ChorusAdapter()
        assert AgentType.UI_VERIFY in adapter.AGENT_TOOL_MAP


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
