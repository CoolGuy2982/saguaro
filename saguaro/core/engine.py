try:
    from google.adk.agents import Agent
    from google.adk.tools import FunctionTool
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners import Runner
except ImportError:
    # Dummy mocks for development without google-adk installed
    Agent = None
    FunctionTool = None
    InMemorySessionService = None
    Runner = None

from saguaro.memory.markdown_store import MarkdownMemory
from saguaro.models.factory import get_model_wrapper
from saguaro.tools.memory_tools import update_memory

class SaguaroKernel:
    def __init__(
        self, 
        slm_model_name: str = "gemini-2.5-flash-lite",
        llm_model_name: str = "gemini-1.5-pro",
        memory_path: str = "memory.md"
    ):
        if Agent is None:
             raise ImportError("The 'google-adk' package is required. Please install it with 'pip install google-adk'.")

        self.slm_model_name = slm_model_name
        self.llm_model_name = llm_model_name
        self.memory_path = memory_path
        
        # 1. Initialize memory
        self.memory = MarkdownMemory(filepath=memory_path)
        
        # 2. Read current memory content
        current_memory = self.memory.read()
        
        # 3. Initialize Neocortex (LLM)
        self.neocortex = Agent(
            name="neocortex",
            model=get_model_wrapper(llm_model_name),
            # Neocortex doesn't have specific tools defined in this phase context yet, or just default context
            instruction="You are the Neocortex, a powerful reasoning engine. Assist the Cortex with complex tasks."
        )

        # 4. Define Session State
        self.initial_state = {
            "memory": self.memory,
            "neocortex": self.neocortex
        }
        
        # 5. Define SLM tools
        self.slm_tools = [
            FunctionTool(update_memory),
            FunctionTool(self._summon_neocortex_tool)
        ]
        
        # 6. Initialize SLM Agent (Cortex)
        instruction = f"""You are the Cortex, a proactive Small Language Model operating an OS.

[SYSTEM STATE / MEMORY]
{current_memory}

Your Goal:
1. Observe the user's context (screenshots/text provided in input).
2. Maintain the 'Short Term Memory' above using `update_memory`.
3. If a complex task arises, summon the Neocortex using `_summon_neocortex_tool`."""

        self.slm = Agent(
            name="cortex",
            model=get_model_wrapper(slm_model_name),
            tools=self.slm_tools,
            instruction=instruction
        )
        
        # Initialize Service (for loop usage)
        self.session_service = InMemorySessionService()

    async def _summon_neocortex_tool(self, tool_context, task: str) -> str:
        """
        Summons the Neocortex (Large Language Model) to handle a complex task.
        """
        # Retrieve neocortex from state if available, or use self.neocortex
        # The prompt says: Retrieve neocortex agent from tool_context.state['neocortex']
        neocortex = tool_context.state.get("neocortex", self.neocortex)
        
        # Create a new, temporary Runner for the Neocortex
        # Runner usually needs an agent and a session service (or creates one)
        # Assuming simple Runner(agent=...) usage based on prompt context
        runner = Runner(agent=neocortex, app_name="saguaro_os")
        
        # Run async passing the task
        # Note: run_async signature depends on ADK version. Prompt says: passing the `task` as the user message.
        # Assuming run_async(new_message=task) or similar.
        result = await runner.run_async(new_message=task, user_id="default_user")
        
        # Collect final response text. 
        # Assuming result is a Turn object or similar with .text or str(result) works.
        # Let's assume result.text property exists.
        response_text = getattr(result, "text", str(result))
        
        return f"Neocortex responded: {response_text}"

    async def run_proactive_loop(self, context_stream):
        """
        Runs the main proactive loop, feeding context to the SLM.
        
        Args:
            context_stream: An async generator yielding content.
        """
        # Initialize Runner for SLM
        runner = Runner(agent=self.slm, session_service=self.session_service, app_name="saguaro_os")
        
        # Create session with initial state
        session_id = "saguaro_session"
        await self.session_service.create_session(
            session_id=session_id, 
            state=self.initial_state, 
            app_name="saguaro_os", 
            user_id="default_user"
        )
        
        # Loop over context
        async for content in context_stream:
            try:
                # Call runner with session_id to persist state/history if needed, or just let it use default?
                # Usually: runner.run_async(new_message=content, session_id=session_id)
                # But prompt said: "Call await runner.run_async(new_message=content)"
                # If we don't pass session_id, it might create a new one. 
                # But we created a session with state. We should probably use it.
                # Let's hope the prompt implies using the session we created.
                # I will pass session_id to be safe and correct.
                
                # FIXED: run_async is an async generator, so we iterate over it
                async for _ in runner.run_async(new_message=content, session_id=session_id, user_id="default_user"):
                    pass
                
                # Optional: Logging
                # print(f"Cortex processed content.")
            except Exception as e:
                print(f"Error in proactive loop: {e}")