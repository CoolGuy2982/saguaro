import time
from collections import deque
from typing import List, Any
from dataclasses import dataclass

@dataclass
class ContextItem:
    timestamp: float
    data: Any # Could be text string or Image object
    token_cost: int

class ContextBuffer:
    def __init__(self, max_tokens: int = 50000):
        self.max_tokens = max_tokens
        self.buffer = deque()
        self.current_tokens = 0

    def add(self, data: Any, token_cost: int = 100):
        """
        Add item to buffer.
        
        Args:
            data: The content (text or image part).
            token_cost: Estimated token cost (default 100 for simplicity if unknown).
        """
        item = ContextItem(timestamp=time.time(), data=data, token_cost=token_cost)
        self.buffer.append(item)
        self.current_tokens += token_cost

        self._trim()

    def _trim(self):
        """Remove old items until we fit in max_tokens."""
        while self.current_tokens > self.max_tokens and self.buffer:
            removed = self.buffer.popleft()
            self.current_tokens -= removed.token_cost

    def get_recent(self, seconds: int = 60) -> List[Any]:
        """Get context items from the last N seconds."""
        now = time.time()
        # Filter items where timestamp > now - seconds
        return [item.data for item in self.buffer if item.timestamp > (now - seconds)]