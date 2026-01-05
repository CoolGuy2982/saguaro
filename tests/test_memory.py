import os
import unittest
import shutil
from saguaro.memory.markdown_store import MarkdownMemory

class TestMarkdownMemory(unittest.TestCase):
    TEST_FILE = "test_brain.md"

    def setUp(self):
        # Ensure clean state
        if os.path.exists(self.TEST_FILE):
            os.remove(self.TEST_FILE)

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.TEST_FILE):
            os.remove(self.TEST_FILE)

    def test_memory_lifecycle(self):
        # 1. Initialize MarkdownMemory with a temporary file
        memory = MarkdownMemory(self.TEST_FILE)
        
        # 2. Check if the file was created with the correct headers
        self.assertTrue(os.path.exists(self.TEST_FILE))
        content = memory.read()
        self.assertIn("# Long Term Memory", content)
        self.assertIn("# Short Term Memory", content)

        # 3. Call append_short_term
        test_message = "User opened VS Code"
        memory.append_short_term(test_message)

        # 4. Read the file back and assert timestamp and text exist under Short Term header
        updated_content = memory.read()
        self.assertIn(test_message, updated_content)
        
        # Verify order: Short Term header comes before the entry
        short_term_idx = updated_content.find("# Short Term Memory")
        entry_idx = updated_content.find(test_message)
        self.assertGreater(entry_idx, short_term_idx, "Entry should be after Short Term Memory header")
        
        # Verify timestamp presence
        # Format: [YYYY-MM-DD HH:MM:SS]
        self.assertRegex(updated_content, r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]")

        # 5. Check get_token_estimate returns a non-zero number
        estimate = memory.get_token_estimate()
        self.assertGreater(estimate, 0)
        print(f"Token estimate: {estimate}")

if __name__ == "__main__":
    unittest.main()
