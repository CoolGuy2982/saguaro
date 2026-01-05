import os
import json
import logging
from typing import List
from datetime import datetime

from .base import BaseMemory
from .schema import MemoryEntry, MemoryType

class SmartMemory(BaseMemory):
    def __init__(self, filepath: str = "memory.md", token_limit: int = 10000):
        self.filepath = filepath
        self.token_limit = token_limit
        self.entries: List[MemoryEntry] = []
        self._initialize_file()
        self.refresh() # Load data into memory

    def _initialize_file(self):
        if not os.path.exists(self.filepath):
            directory = os.path.dirname(self.filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
            # Create empty file
            self._save_to_disk()

    def refresh(self):
        """Re-read from disk to sync state."""
        self.entries = self._parse_markdown(self.filepath)

    def read(self) -> str:
        """
        Returns a human-readable string of memories for the LLM context.
        It sorts Long Term first, then Short Term.
        """
        self.refresh()
        
        long_term = [e.content for e in self.entries if e.memory_type == MemoryType.LONG_TERM]
        short_term = [e.content for e in self.entries if e.memory_type == MemoryType.SHORT_TERM]
        
        return f"""# Long Term Memory
{chr(10).join(long_term)}

# Short Term Memory
{chr(10).join(short_term)}"""

    def write(self, content: str):
        """
        Overwrites memory. Not recommended for SmartMemory, 
        but kept for BaseMemory compatibility. 
        Treats the content as a single new Short Term entry.
        """
        self.entries = [MemoryEntry(content=content, memory_type=MemoryType.SHORT_TERM)]
        self._save_to_disk()

    def append_short_term(self, content: str):
        """Adds a new short term memory entry."""
        # Check if identical entry exists to avoid duplicates, just update access
        for entry in self.entries:
            if entry.content == content and entry.memory_type == MemoryType.SHORT_TERM:
                entry.update_access()
                self._save_to_disk()
                return

        new_entry = MemoryEntry(content=content, memory_type=MemoryType.SHORT_TERM)
        self.entries.append(new_entry)
        
        # Trigger lifecycle management
        self._consolidate()
        self._prune()
        
        self._save_to_disk()

    def delete_entry(self, content_substring: str):
        """Forget logic: Remove entries containing specific text."""
        initial_count = len(self.entries)
        self.entries = [e for e in self.entries if content_substring not in e.content]
        if len(self.entries) < initial_count:
            self._save_to_disk()

    def get_token_estimate(self) -> int:
        # Rough estimate: 4 chars per token
        text_content = "".join([e.content for e in self.entries])
        return len(text_content) // 4

    def _parse_markdown(self, filepath: str) -> List[MemoryEntry]:
        """
        Parses the markdown file. Looks for HTML comments containing JSON metadata.
        If no metadata is found (legacy format), creates default entries.
        """
        if not os.path.exists(filepath):
            return []

        entries = []
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_meta = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for metadata comment
            if line.startswith("<!--") and line.endswith("-->"):
                try:
                    json_str = line[4:-3]
                    current_meta = json.loads(json_str)
                except:
                    current_meta = None
                continue
            
            # Ignore headers
            if line.startswith("# "):
                continue

            # Process Content Line
            if current_meta:
                # Reconstruct entry from metadata + content
                try:
                    entry = MemoryEntry(**current_meta)
                    entry.content = line # Ensure content matches text (source of truth)
                    entries.append(entry)
                except:
                    # Fallback if schema changed
                    entries.append(MemoryEntry(content=line))
                current_meta = None
            else:
                # Legacy line support
                entries.append(MemoryEntry(content=line))

        return entries

    def _save_to_disk(self):
        """Serializes entries to Markdown with embedded Metadata."""
        lines = []
        
        lines.append("# Long Term Memory")
        for entry in self.entries:
            if entry.memory_type == MemoryType.LONG_TERM:
                json_meta = entry.model_dump_json()
                lines.append(f"<!-- {json_meta} -->")
                lines.append(entry.content)
                lines.append("") # Spacer

        lines.append("\n# Short Term Memory")
        for entry in self.entries:
            if entry.memory_type == MemoryType.SHORT_TERM:
                json_meta = entry.model_dump_json()
                lines.append(f"<!-- {json_meta} -->")
                lines.append(entry.content)
                lines.append("")

        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _prune(self):
        """
        Deletes lowest scoring Short Term memories until under token limit.
        """
        current_tokens = self.get_token_estimate()
        if current_tokens <= self.token_limit:
            return

        # Separate types
        short_terms = [e for e in self.entries if e.memory_type == MemoryType.SHORT_TERM]
        long_terms = [e for e in self.entries if e.memory_type == MemoryType.LONG_TERM]

        # Sort short terms by score (lowest first)
        short_terms.sort(key=lambda x: x.score)

        # Remove items until we fit or run out of short term memory
        while self.get_token_estimate() > self.token_limit and short_terms:
            removed = short_terms.pop(0) # Remove lowest score
            # Reconstruct entries list
            self.entries = long_terms + short_terms
            
        logging.info(f"Pruned memory to {self.get_token_estimate()} tokens.")

    def _consolidate(self):
        """
        Moves Short Term memories to Long Term if they are accessed often.
        Threshold: Accessed more than 5 times.
        """
        for entry in self.entries:
            if entry.memory_type == MemoryType.SHORT_TERM and entry.access_count > 5:
                entry.memory_type = MemoryType.LONG_TERM
                logging.info(f"Consolidated memory to Long Term: {entry.content[:30]}...")