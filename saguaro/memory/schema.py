from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class MemoryType(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"

class MemoryEntry(BaseModel):
    """
    Represents a single unit of memory (a thought, observation, or fact).
    Metadata allows for neuro-symbolic management (pruning/consolidation).
    """
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: datetime = Field(default_factory=datetime.now)
    access_count: int = 1
    memory_type: MemoryType = MemoryType.SHORT_TERM

    def update_access(self):
        """
        Call this when the memory is retrieved or reinforced.
        Updates the timestamp and increments the usage counter.
        """
        self.last_accessed = datetime.now()
        self.access_count += 1

    @property
    def score(self) -> float:
        """
        Calculate a relevance score.
        Simple heuristic: frequency * recency_weight
        (This can be made more complex later).
        """
        # Simple decay: older items get lower scores unless accessed frequently
        age_in_hours = (datetime.now() - self.last_accessed).total_seconds() / 3600
        # Avoid division by zero, min age 1 hour for decay calc
        decay = 1 / (max(age_in_hours, 1)) 
        return self.access_count * decay