import os
import datetime
from .base import BaseMemory

class MarkdownMemory(BaseMemory):
    def __init__(self, filepath: str = "memory.md"):
        self.filepath = filepath
        self._initialize_file()

    def _initialize_file(self):
        if not os.path.exists(self.filepath):
            # Create directory if it doesn't exist (just in case filepath has dirs)
            directory = os.path.dirname(self.filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
                
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write("# Long Term Memory\n\n# Short Term Memory\n")

    def read(self) -> str:
        if not os.path.exists(self.filepath):
            return ""
        with open(self.filepath, "r", encoding="utf-8") as f:
            return f.read()

    def write(self, content: str):
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def append_short_term(self, content: str):
        """
        Appends a new line to the # Short Term Memory section.
        Adds a timestamp to the entry.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {content}"
        
        # We assume Short Term Memory is at the end of the file based on initialization.
        # To be safe and ensure we are appending to the Short Term section, 
        # we could check the file content, but for this phase, appending to the end is the intended behavior
        # given the structure # Long Term ... # Short Term ...
        
        current_content = self.read()
        
        # Ensure we have a newline separator if the file is not empty and doesn't end with one
        prefix = ""
        if current_content and not current_content.endswith("\n"):
            prefix = "\n"
            
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(f"{prefix}{entry}\n")

    def get_token_estimate(self) -> int:
        content = self.read()
        return len(content) // 4
