try:
    from google.adk.tools import ToolContext
except ImportError:
    ToolContext = None

async def update_memory(tool_context: ToolContext, action: str, content: str) -> str:
    """
    Updates the memory of the system.

    Args:
        tool_context: The tool execution context provided by the ADK.
        action: "append_short_term" (default) or "forget" (delete specific concept).
        content: The content to remember or the keyword to forget.

    Returns:
        str: Result status.
    """
    if "memory" not in tool_context.state:
        return "Error: Memory system not accessible."

    memory = tool_context.state["memory"]

    if action == "append_short_term" or action == "add":
        memory.append_short_term(content)
        return "Memory appended (Short Term)."

    elif action == "forget":
        # New capability: Active Forgetting
        memory.delete_entry(content)
        return f"Removed memories containing: '{content}'"

    else:
        return f"Error: Unknown action '{action}'."

async def retrieve_context(tool_context: ToolContext, lookback_seconds: int = 60) -> str:
    """
    Retrieves raw sensory data from the recent past (Sliding Window).
    Useful if the agent needs to see what happened just before the current event.

    Args:
        tool_context: Context.
        lookback_seconds: How far back to look (default 60s).

    Returns:
        str: Summary of context items.
    """
    if "context_buffer" not in tool_context.state:
        return "Error: Context Buffer not accessible."

    buffer = tool_context.state["context_buffer"]
    items = buffer.get_recent(seconds=lookback_seconds)
    
    return f"Retrieved {len(items)} context items from last {lookback_seconds} seconds."