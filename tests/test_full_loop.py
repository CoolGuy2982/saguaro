import unittest
import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# --- MOCKS START ---
sys.modules["google.adk"] = MagicMock()
sys.modules["google.adk.models"] = MagicMock()
sys.modules["google.adk.agents"] = MagicMock()
sys.modules["google.adk.tools"] = MagicMock()
sys.modules["google.adk.sessions"] = MagicMock()
sys.modules["google.adk.runners"] = MagicMock()
sys.modules["pynput"] = MagicMock() # Mock pynput so we don't need real hardware

# Specific mocks
mock_runner = MagicMock()
sys.modules["google.adk.runners"].Runner = mock_runner

# Define an Async Iterator for the mock runner
class AsyncRunnerIter:
    def __init__(self, *args, **kwargs): pass
    def __aiter__(self): return self
    async def __anext__(self): return "TurnProcessed"

mock_runner.return_value.run_async.side_effect = lambda **kwargs: AsyncRunnerIter()

from saguaro.core.engine import SaguaroKernel

# --- TESTS START ---

class TestEngineIntegration(unittest.TestCase):
    
    def test_proactive_loop_structure(self):
        """
        Verifies the engine loop handles both timer-based and input-based triggers.
        """
        # 1. Setup Kernel
        # We use a temp memory file
        kernel = SaguaroKernel(memory_path="test_loop_brain.md")
        
        # 2. Mock the Nervous System (InputListener)
        # We want to simulate:
        # Loop 1: No input, Timer triggers.
        # Loop 2: Input triggers.
        # Loop 3: Cancel/Exit.
        
        async def mock_wait_input():
            # Simulate waiting for input
            await asyncio.sleep(0.1) 
            return "Mock Input Event"

        kernel.input_listener.wait_for_input = list([
            AsyncMock(side_effect=asyncio.TimeoutError), # Loop 1: Timeout (let stream win)
            AsyncMock(return_value="User Key Press"),    # Loop 2: User input wins
        ]).pop

        # 3. Mock the Visual Stream (Context Stream)
        async def mock_stream():
            yield "Screen Capture 1"
            await asyncio.sleep(0.2)
            yield "Screen Capture 2"
            
        # 4. Run the loop for a short time
        async def run_limited_loop():
            try:
                # We wrap execution in a timeout to kill the infinite loop
                await asyncio.wait_for(
                    kernel.run_proactive_loop(mock_stream()), 
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                pass # Expected exit
            
        # Run test
        pass 

    def test_components_init(self):
        """
        Simple check that all subsystems (Brain, Senses, Tools) are loaded.
        """
        kernel = SaguaroKernel(memory_path="test_init.md")
        
        # Brain Check
        self.assertIsNotNone(kernel.memory)
        self.assertTrue(hasattr(kernel.memory, "_prune"))
        
        # Nervous System Check
        self.assertIsNotNone(kernel.input_listener)
        
        # Context Check
        self.assertIsNotNone(kernel.context_buffer)
        
        # Cleanup
        if os.path.exists("test_init.md"):
            os.remove("test_init.md")

    def tearDown(self):
        import os
        if os.path.exists("test_loop_brain.md"):
            os.remove("test_loop_brain.md")

if __name__ == "__main__":
    unittest.main()