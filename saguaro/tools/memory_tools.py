try:
    from google.adk.tools import ToolContext
except ImportError:
    ToolContext = None

async def update_memory(tool_context: ToolContext, action: str, content: str) -> str:
    """
    Updates the memory of the system.

    Args:
        tool_context: The tool execution context provided by the ADK.
        action: The action to perform. Either "add_long_term" or "append_short_term".
        content: The content to write or append to memory.

    Returns:
        str: A status message indicating the result of the operation.
    """
    if "memory" not in tool_context.state:
        return "Error: Memory system not accessible."

    memory = tool_context.state["memory"]

    if action == "add_long_term":
        # In a real scenario, this might append to long term section specifically.
        # For now, per instruction, we use write() or similar, 
        # but the prompt said "Call memory.write(content)". 
        # However, earlier memory.write OVERWRITES the file.
        # "In a real app we'd append, but for now write/append to long term logic"
        # Let's stick to the prompt's loose instruction but maybe make it safer if possible,
        # or just follow "Call memory.write(content)".
        # Actually, let's look at BaseMemory: write(content) overwrites.
        # If the SLM calls this, it might wipe memory. 
        # But I must follow instructions: "If action == 'add_long_term': Call memory.write(content)"
        memory.write(content)
        return "Long term memory updated (overwritten)."

    elif action == "append_short_term":
        memory.append_short_term(content)
        return "Entry appended to short term memory."

    else:
        return f"Error: Unknown action '{action}'."
