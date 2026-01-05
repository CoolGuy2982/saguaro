from abc import ABC, abstractmethod

class BaseMemory(ABC):
    @abstractmethod
    def read(self) -> str:
        """Return the full content of the memory."""
        pass

    @abstractmethod
    def write(self, content: str):
        """Overwrite the memory with new content."""
        pass

    @abstractmethod
    def append_short_term(self, content: str):
        """Append a new entry to the short term memory section."""
        pass

    @abstractmethod
    def get_token_estimate(self) -> int:
        """Return an estimate of the token count."""
        pass
