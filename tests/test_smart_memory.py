import unittest
import os
import time
from saguaro.memory.smart_store import SmartMemory
from saguaro.memory.schema import MemoryType

class TestSmartMemory(unittest.TestCase):
    TEST_FILE = "test_smart_brain.md"

    def setUp(self):
        if os.path.exists(self.TEST_FILE):
            os.remove(self.TEST_FILE)
        # Initialize with a small token limit to test pruning easily
        self.memory = SmartMemory(filepath=self.TEST_FILE, token_limit=100)

    def tearDown(self):
        if os.path.exists(self.TEST_FILE):
            os.remove(self.TEST_FILE)

    def test_persistence_with_metadata(self):
        """Test that metadata (access count, type) survives round-trip to disk."""
        # 1. Add an entry
        content = "User is coding in Python"
        self.memory.append_short_term(content)
        
        # 2. Modify metadata manually (simulate usage)
        self.memory.entries[0].access_count = 10
        self.memory._save_to_disk()
        
        # 3. Reload from disk
        new_memory = SmartMemory(filepath=self.TEST_FILE)
        loaded_entry = new_memory.entries[0]
        
        # 4. Assertions
        self.assertEqual(loaded_entry.content, content)
        self.assertEqual(loaded_entry.access_count, 10)
        self.assertEqual(loaded_entry.memory_type, MemoryType.SHORT_TERM)

    def test_pruning_logic(self):
        """Test that low-score memories are deleted when limit is exceeded."""
        # Limit is 100 tokens (approx 400 chars).
        # We will add 5 entries of 100 chars each.
        
        long_entry = "A" * 100
        
        # Add 5 entries
        for i in range(5):
            self.memory.append_short_term(f"{i}_{long_entry}")
            # Simulate different importance: Entry 4 is accessed a lot
            if i == 4:
                for _ in range(20): 
                    self.memory.entries[-1].update_access()
        
        # Force save and refresh to trigger pruning logic inside append/save cycle
        # (In SmartMemory, _prune is called during append_short_term)
        
        # Current state: The last append should have triggered pruning.
        # Total size ~500 chars > 100 token limit.
        # It should delete the ones with lowest scores (access_count=1).
        
        remaining = self.memory.entries
        
        # We expect fewer than 5 entries
        self.assertLess(len(remaining), 5)
        
        # We expect entry 4 (high access) to survive
        contents = [e.content for e in remaining]
        self.assertTrue(any(f"4_{long_entry}" in c for c in contents))

    def test_consolidation(self):
        """Test moving Short Term to Long Term."""
        content = "Important Fact"
        self.memory.append_short_term(content)
        
        # Artificially boost access count
        self.memory.entries[0].access_count = 10
        
        # Trigger consolidation manually for test
        self.memory._consolidate()
        
        self.assertEqual(self.memory.entries[0].memory_type, MemoryType.LONG_TERM)

if __name__ == "__main__":
    unittest.main()