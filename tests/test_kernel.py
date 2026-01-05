import unittest
import sys
from unittest.mock import MagicMock, patch

# Mock google.adk modules BEFORE importing saguaro modules that depend on them
sys.modules["google.adk"] = MagicMock()
sys.modules["google.adk.models"] = MagicMock()
sys.modules["google.adk.models.lite_llm"] = MagicMock()
sys.modules["google.adk.agents"] = MagicMock()

# Setup specific mocks
mock_lite_llm = MagicMock()
sys.modules["google.adk.models.lite_llm"].LiteLlm = mock_lite_llm

mock_agent = MagicMock()
sys.modules["google.adk.agents"].Agent = mock_agent

# Now we can import the modules to test
from saguaro.models.factory import get_model_wrapper
from saguaro.core.engine import SaguaroKernel

class TestKernel(unittest.TestCase):
    
    def test_factory(self):
        # Assert get_model_wrapper("gemini-1.5") returns a string
        self.assertEqual(get_model_wrapper("gemini-1.5"), "gemini-1.5")
        
        # Assert get_model_wrapper("openai/gpt-4") returns a LiteLlm object
        # Since we mocked LiteLlm, it should return an instance of the mock
        result = get_model_wrapper("openai/gpt-4")
        self.assertTrue(isinstance(result, MagicMock)) 
        # Verify LiteLlm was called with the correct argument
        mock_lite_llm.assert_called_with(model="openai/gpt-4")

    def test_kernel_integration(self):
        test_memory_file = "test_memory_kernel.md"
        
        # Create a temporary memory.md with dummy content
        with open(test_memory_file, "w", encoding="utf-8") as f:
            f.write("# Long Term Memory\nUser loves Python")
            
        try:
            # Initialize SaguaroKernel pointing to that file
            kernel = SaguaroKernel(memory_path=test_memory_file)
            
            # Assertion: Check kernel.slm.instruction contains the string "User loves Python"
            # kernel.slm is a mock Agent instance. We need to check the arguments passed to Agent constructor.
            # The Agent constructor was called during SaguaroKernel.__init__
            
            # Get the call args of the Agent mock
            # Agent(name="cortex", model=..., tools=..., instruction=...)
            call_args = mock_agent.call_args
            _, kwargs = call_args
            
            instruction = kwargs.get("instruction", "")
            self.assertIn("User loves Python", instruction)
            self.assertIn("You are the Cortex", instruction)
            
        finally:
            # Clean up the temporary file
            import os
            if os.path.exists(test_memory_file):
                os.remove(test_memory_file)

if __name__ == "__main__":
    unittest.main()
