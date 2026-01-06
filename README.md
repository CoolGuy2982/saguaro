# 🌵 Saguaro 🌵

Saguaro is a neuro symbolic proactive OS library built on the Google Agent Development Kit (ADK). It is designed to create proactive AI systems that act as a "Cortex" (SLM) and "Neocortex" (LLM) for your applications.

## Installation

```bash
pip install saguaro
```

# Features
Proactive Loop: Automatically monitors input streams (visual, audio, or data) and user activity.

Neuro-Symbolic Memory: Manages Short-Term and Long-Term memory with automatic pruning and consolidation.

Model Agnostic: Works with Google Gemini, OpenAI, Anthropic, or local models via LiteLlm.

Input Agnostic: Inject any nervous system (WebSocket, REST API, etc.) to drive the agent.

# Usage
```python
import asyncio
from saguaro import SaguaroKernel

async def main():
    kernel = SaguaroKernel(
        slm_model_name="gemini-2.5-flash-lite",
        llm_model_name="gemini-2.5-pro"
    )
    # Your event loop logic here
```