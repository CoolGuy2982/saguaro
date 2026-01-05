import unittest
import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Mock google.adk modules
sys.modules["google.adk"] = MagicMock()
sys.modules["google.adk.models"] = MagicMock()
sys.modules["google.adk.models.lite_llm"] = MagicMock()
sys.modules["google.adk.agents"] = MagicMock()
sys.modules["google.adk.tools"] = MagicMock()
sys.modules["google.adk.sessions"] = MagicMock()
sys.modules["google.adk.runners"] = MagicMock()

# Specific mocks
mock_tool_context_cls = MagicMock()
sys.modules["google.adk.tools"].ToolContext = mock_tool_context_cls

mock_function_tool = MagicMock()
sys.modules["google.adk.tools"].FunctionTool = mock_function_tool

mock_agent = MagicMock()
sys.modules["google.adk.agents"].Agent = mock_agent

mock_session_service = MagicMock()
sys.modules["google.adk.sessions"].InMemorySessionService = mock_session_service

mock_runner = MagicMock()
sys.modules["google.adk.runners"].Runner = mock_runner

# Import Saguaro modules
from saguaro.tools.memory_tools import update_memory
from saguaro.core.engine import SaguaroKernel

class TestFullLoop(unittest.TestCase):
    
    def test_memory_tool(self):
        # 1. Test Tools
        # Mock ToolContext
        mock_context = MagicMock()
        mock_memory = MagicMock()
        mock_context.state = {'memory': mock_memory}
        
        # Call update_memory
        async def run_tool():
            return await update_memory(mock_context, 'append_short_term', 'test log')
        
        result = asyncio.run(run_tool())
        
        # Assert memory append was called
        mock_memory.append_short_term.assert_called_with('test log')
        self.assertEqual(result, "Entry appended to short term memory.")

    def test_kernel_wiring(self):
        # 2. Test Kernel Wiring
        # Need to ensure imports inside engine.py use the mocks
        
        # Test file mocking
        test_memory_file = "test_memory_loop.md"
        with open(test_memory_file, "w", encoding="utf-8") as f:
            f.write("# Long Term Memory\n")
            
        try:
            kernel = SaguaroKernel(memory_path=test_memory_file)
            
            # Check kernel.slm.tools has 2 items
            # kernel.slm is the mock Agent.
            # We access the call args used to create it.
            # Agent(..., tools=...)
            call_args = mock_agent.call_args_list[-1] # The last call should be the SLM (after Neocortex)
            _, kwargs = call_args
            
            tools = kwargs.get("tools", [])
            self.assertEqual(len(tools), 2)
            
            # Verify initial_state contains memory
            self.assertIn("memory", kernel.initial_state)
            self.assertIn("neocortex", kernel.initial_state)
            self.assertEqual(kernel.initial_state["memory"], kernel.memory)
            
        finally:
            import os
            if os.path.exists(test_memory_file):
                os.remove(test_memory_file)

if __name__ == "__main__":
    unittest.main()
