import asyncio
import io
import mss
from PIL import Image
from google.genai import types

class ScreenStreamer:
    def __init__(self, interval: float = 2.0, resize_factor: float = 0.5):
        """
        Initialize the ScreenStreamer.
        
        Args:
            interval (float): Time in seconds between captures.
            resize_factor (float): Not explicitly used in the logic described, 
                                   but kept for API compatibility if needed.
                                   The logic enforces max width 1024px.
        """
        self.interval = interval
        self.sct = mss.mss()

    def _process_image(self, sct_img) -> bytes:
        """
        Convert mss image to optimized JPEG bytes.
        """
        # Convert to PIL Image
        # MSS `grab` returns an object with `bgra` data usually
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        
        # Optimization: Resize if width > 1024px
        if img.width > 1024:
            aspect_ratio = img.height / img.width
            new_width = 1024
            new_height = int(new_width * aspect_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        # Save to BytesIO as JPEG
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        return buffer.getvalue()

    def capture(self) -> types.Part:
        """
        Capture the screen and return a genai Part object.
        """
        # Capture primary monitor (monitor 1)
        sct_img = self.sct.grab(self.sct.monitors[1])
        
        image_bytes = self._process_image(sct_img)
        
        return types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

    async def stream(self):
        """
        Async generator yielding Content objects with screen captures.
        """
        while True:
            try:
                part = self.capture()
                yield types.Content(role="user", parts=[part])
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
