import time
import asyncio
import logging
from typing import Optional

try:
    from pynput import keyboard, mouse
except ImportError:
    keyboard = None
    mouse = None
    logging.warning("pynput not found. Input monitoring will be disabled.")

class InputListener:
    def __init__(self, debounce_seconds: float = 1.0, loop: Optional[asyncio.AbstractEventLoop] = None):
        """
        Monitors Keyboard and Mouse inputs.
        
        Args:
            debounce_seconds: Minimum time between triggers to avoid flooding.
            loop: The asyncio loop to push events to.
        """
        self.debounce_seconds = debounce_seconds
        self.last_trigger = 0.0
        self.loop = loop or asyncio.get_event_loop()
        self.event_queue = asyncio.Queue()
        self.active = False
        
        self.kb_listener = None
        self.mouse_listener = None

    def start(self):
        if not keyboard or not mouse:
            return

        self.active = True
        self.kb_listener = keyboard.Listener(on_press=self._on_activity)
        self.mouse_listener = mouse.Listener(on_click=self._on_activity)
        
        self.kb_listener.start()
        self.mouse_listener.start()
        logging.info("Nervous system (InputListener) active.")

    def stop(self):
        self.active = False
        if self.kb_listener: self.kb_listener.stop()
        if self.mouse_listener: self.mouse_listener.stop()

    def _on_activity(self, *args):
        """Callback for pynput threads."""
        if not self.active:
            return

        now = time.time()
        if now - self.last_trigger > self.debounce_seconds:
            self.last_trigger = now
            # Schedule the event safely in the asyncio loop
            self.loop.call_soon_threadsafe(self.event_queue.put_nowait, "user_activity")

    async def wait_for_input(self):
        """Async wait for the next input event."""
        return await self.event_queue.get()