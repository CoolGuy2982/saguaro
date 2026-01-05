import asyncio
import os
import logging
from saguaro.core.engine import SaguaroKernel
from saguaro.senses.visual import ScreenStreamer

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration Constants
SLM_MODEL = "gemini-2.5-flash-lite"
LLM_MODEL = "gemini-2.5-pro"
MEMORY_FILE = "my_brain.md"

async def main():
    # Step 1: Initialize Kernel
    try:
        kernel = SaguaroKernel(
            slm_model_name=SLM_MODEL,
            llm_model_name=LLM_MODEL,
            memory_path=MEMORY_FILE
        )
    except ImportError as e:
        logging.error(f"Initialization Failed: {e}")
        print(f"❌ Critical Error: {e}")
        return

    # Step 2: Initialize Senses
    # Default interval 5.0s, resize factor 0.5
    eyes = ScreenStreamer(interval=5.0, resize_factor=0.5)

    # Step 3: Startup Message
    print("🌵 Saguaro OS Online. Watching screen...")
    logging.info(f"Saguaro started. Cortex: {SLM_MODEL}, Neocortex: {LLM_MODEL}")

    # Step 4: Run Proactive Loop
    try:
        # Pass the visual stream to the kernel
        await kernel.run_proactive_loop(context_stream=eyes.stream())
    except asyncio.CancelledError:
        logging.info("Loop cancelled.")
    except KeyboardInterrupt:
        # This catch might be redundant if caught in __main__, but good for loop scope
        print("\n🛑 Saguaro OS shutting down...")
    except Exception as e:
        logging.error(f"Unexpected error in loop: {e}")
    finally:
        print("Goodbye.")

if __name__ == "__main__":
    if "GOOGLE_API_KEY" not in os.environ:
        print("⚠️  WARNING: GOOGLE_API_KEY not found in environment.")
        # Proceeding anyway as requested

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Saguaro OS shutting down forcefully...")
