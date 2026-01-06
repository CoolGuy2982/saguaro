import asyncio
import logging
from typing import Optional, Any

try:
    from google.adk.agents import Agent
    from google.adk.tools import FunctionTool
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners import Runner
except ImportError:
    Agent = None
    FunctionTool = None
    InMemorySessionService = None
    Runner = None

from saguaro.memory.base import BaseMemory
from saguaro.memory.smart_store import SmartMemory
from saguaro.models.factory import get_model_wrapper
from saguaro.tools.memory_tools import update_memory, retrieve_context
from saguaro.senses.inputs import InputListener
from saguaro.core.context import ContextBuffer

class SaguaroKernel:
    def __init__(
        self, 
        slm_model_name: str = "gemini-2.5-flash-lite",
        llm_model_name: str = "gemini-2.5-pro",
        memory_path: str = "memory.md",
        memory_backend: Optional[BaseMemory] = None,
        nervous_system: Optional[Any] = None
    ):
        """
        Initialize the Saguaro Kernel.

        Args:
            slm_model_name: Name of the SLM (Cortex).
            llm_model_name: Name of the LLM (Neocortex).
            memory_path: Default local file path if no backend is provided.
            memory_backend: Custom memory storage instance (e.g. Firestore, Redis).
                            Must inherit from BaseMemory.
            nervous_system: Custom input event listener (e.g. WebSocket handler).
                            Must implement .start() and async .wait_for_input().
                            Defaults to local Keyboard/Mouse listener if None.
        """
        if Agent is None:
             raise ImportError("The 'google-adk' package is required.")

        self.slm_model_name = slm_model_name
        
        # 1. Initialize Memory
        # Dependency Injection: Use provided backend or fall back to SmartMemory
        if memory_backend:
            self.memory = memory_backend
        else:
            self.memory = SmartMemory(filepath=memory_path)

        self.context_buffer = ContextBuffer(max_tokens=50000)
        
        # 2. Initialize Nervous System (Inputs)
        # Dependency Injection: Use provided input system or fall back to local InputListener
        if nervous_system:
            self.input_listener = nervous_system
        else:
            self.input_listener = InputListener()
        
        # 3. Initialize Neocortex (LLM)
        self.neocortex = Agent(
            name="neocortex",
            model=get_model_wrapper(llm_model_name),
            instruction="You are the Neocortex. Assist the Cortex with complex reasoning tasks."
        )

        # 4. Define Session State
        self.initial_state = {
            "memory": self.memory,
            "neocortex": self.neocortex,
            "context_buffer": self.context_buffer,
            "neocortex_status": "idle" # Track if LLM is busy
        }
        
        # 5. Define SLM Tools
        self.slm_tools = [
            FunctionTool(update_memory),
            FunctionTool(retrieve_context),
            FunctionTool(self._summon_neocortex_tool)
        ]
        
        # 6. Initialize Cortex (SLM)
        instruction = """You are the Cortex, a proactive OS agent.
Your Goal:
1. Continuous Observation: You receive updates when the user acts.
2. Memory Management: Use `update_memory` to log important tasks/context.
3. Context Retrieval: If you are unsure what happened previously, use `retrieve_context`.
4. Delegation: If a task is complex, summon the Neocortex."""

        self.slm = Agent(
            name="cortex",
            model=get_model_wrapper(slm_model_name),
            tools=self.slm_tools,
            instruction=instruction
        )
        
        self.session_service = InMemorySessionService()

    async def _summon_neocortex_tool(self, tool_context, task: str) -> str:
        """Summons the Neocortex (LLM) for complex tasks."""
        tool_context.state["neocortex_status"] = "busy"
        neocortex = tool_context.state.get("neocortex")
        
        try:
            # Create a runner for the specific task
            runner = Runner(agent=neocortex, app_name="saguaro_os")
            
            # Simple run execution
            response_text = ""
            async for turn in runner.run_async(new_message=task, user_id="default_user"):
                # Assuming turn has text or we accumulate it
                try:
                    response_text = turn.text
                except:
                    pass
            
            tool_context.state["neocortex_status"] = "idle"
            return f"Neocortex processed task. Response: {response_text}"
        except Exception as e:
            tool_context.state["neocortex_status"] = "error"
            return f"Neocortex failed: {e}"

    async def run_proactive_loop(self, context_stream):
        """
        The Heartbeat Loop.
        Waits for EITHER a time interval (via context_stream) OR user input.
        """
        # Start the listener (custom or default)
        if hasattr(self.input_listener, 'start'):
            self.input_listener.start()
        
        runner = Runner(agent=self.slm, session_service=self.session_service, app_name="saguaro_os")
        session_id = "saguaro_main_session"
        await self.session_service.create_session(
            session_id=session_id, 
            state=self.initial_state, 
            app_name="saguaro_os",
            user_id="default_user"
        )
        
        # Get the iterator for the visual stream (time based)
        stream_iter = context_stream.__aiter__()
        
        logging.info("Core loop starting. Waiting for stimuli...")

        while True:
            try:
                # Create tasks for both triggers
                input_task = asyncio.create_task(self.input_listener.wait_for_input())
                stream_task = asyncio.create_task(stream_iter.__anext__())
                
                # Wait for FIRST completed
                done, pending = await asyncio.wait(
                    [input_task, stream_task], 
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                content_to_send = None
                
                # Check what triggered
                if input_task in done:
                    # Generic Input Trigger:
                    # Pass the raw result through. This supports text, objects, 
                    # audio bytes, or images provided by the backend nervous system.
                    content_to_send = input_task.result()
                
                if stream_task in done:
                    # Timer fired -> Periodic Check
                    content_to_send = stream_task.result()

                # Add to Context Buffer
                if content_to_send:
                    # Calculate cost approx
                    cost = 1000 if not isinstance(content_to_send, str) else len(content_to_send)//4
                    self.context_buffer.add(content_to_send, token_cost=cost)
                
                # Inject Memory Context into the prompt
                # We can prepend the current memory state to the message
                current_memory_snapshot = self.memory.read()
                
                # Construct the message wrapper
                # The ADK Runner handles lists of mixed content (Text, Images, Blobs)
                message_payload = [
                    f"CONTEXT_MEMORY:\n{current_memory_snapshot}",
                    content_to_send
                ]
                
                async for _ in runner.run_async(new_message=message_payload, session_id=session_id, user_id="default_user"):
                    pass

                # Clean up pending tasks
                for task in pending:
                    # If we processed input, the stream task is still pending. 
                    # We shouldn't cancel it usually, as it's an interval.
                    # But for simplicity here we assume we catch it next loop or simple loop logic.
                    if task == stream_task:
                        # We need to preserve this task for next iteration if it wasn't done
                        # This gets complex. Simplified: Cancel pending and restart loop logic.
                        # Ideally we wouldn't cancel the generator. 
                        pass 
                    else:
                        task.cancel()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in loop: {e}")
                await asyncio.sleep(1) # Backoff