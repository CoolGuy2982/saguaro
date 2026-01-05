import unittest
import sys
import asyncio
from unittest.mock import MagicMock, patch

# 1. Mock libraries that might not be present or need valid display environment
sys.modules["mss"] = MagicMock()
sys.modules["google.genai"] = MagicMock()
sys.modules["google.genai.types"] = MagicMock()

# Setup mocks
mock_mss_class = sys.modules["mss"].mss
mock_mss_instance = mock_mss_class.return_value

# Link the types module explicitly to the parent package mock
# to ensure 'from google.genai import types' gets the same object
sys.modules["google.genai"].types = sys.modules["google.genai.types"]

mock_types = sys.modules["google.genai.types"]
# Mock Part.from_bytes and Content
mock_part_from_bytes = MagicMock()
mock_types.Part.from_bytes = mock_part_from_bytes

# Mocking Content class
class MockContent:
    def __init__(self, role, parts):
        self.role = role
        self.parts = parts
mock_types.Content = MockContent

# Now import the module to test
from saguaro.senses.visual import ScreenStreamer

class TestSenses(unittest.TestCase):
    
    def setUp(self):
        # Reset mocks
        mock_mss_instance.reset_mock()
        mock_part_from_bytes.reset_mock()

    def test_processing_resize(self):
        # Setup a mock sct_img
        # We need it to be compatible with Image.frombytes("RGB", size, bgra, "raw", "BGRX")
        # Create a fake big image 2000x1000
        width = 2000
        height = 1000
        size = (width, height)
        # 4 bytes per pixel for BGRA
        bgra = b'\x00' * (width * height * 4) 
        
        mock_sct_img = MagicMock()
        mock_sct_img.size = size
        mock_sct_img.bgra = bgra
        
        # We need separate verify logic because _process_image creates a new Image and resizes it.
        # We can mock PIL.Image.frombytes to return a mock Image, then track calls to resize.
        
        with patch("PIL.Image.frombytes") as mock_frombytes:
            mock_img = MagicMock()
            mock_img.width = 2000
            mock_img.height = 1000
            mock_frombytes.return_value = mock_img
            
            # Mock the resize return value
            mock_resized_img = MagicMock()
            mock_img.resize.return_value = mock_resized_img
            
            streamer = ScreenStreamer()
            result_bytes = streamer._process_image(mock_sct_img)
            
            # Verify resize was called
            # Target width 1024
            # Aspect ratio 1000/2000 = 0.5
            # New height = 1024 * 0.5 = 512
            mock_img.resize.assert_called()
            args, _ = mock_img.resize.call_args
            self.assertEqual(args[0], (1024, 512))
            
            # Verify save was called on the resized image
            mock_resized_img.save.assert_called()

    def test_stream(self):
        # Mock capture dependencies
        # Monitors list
        mock_mss_instance.monitors = [{}, {}] # monitors[1] exists
        
        # Mock grab return
        mock_sct_img = MagicMock()
        mock_sct_img.size = (100, 100) # Small image, no resize
        mock_sct_img.bgra = b'\x00' * (100 * 100 * 4)
        mock_mss_instance.grab.return_value = mock_sct_img
        
        async def run_stream():
            streamer = ScreenStreamer(interval=0.1)
            count = 0
            
            # PATCH ADDED: Ensure the imported types.Content is our MockContent class
            with patch("saguaro.senses.visual.types.Content", side_effect=MockContent):
                async for content in streamer.stream():
                    count += 1
                    self.assertIsInstance(content, MockContent)
                    self.assertEqual(content.role, "user")
                    if count >= 2:
                        break
        
        # Use asyncio.run to execute the async test
        asyncio.run(run_stream())

if __name__ == "__main__":
    unittest.main()