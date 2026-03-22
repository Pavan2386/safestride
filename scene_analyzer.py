"""
scene_analyzer.py
SceneAnalyzer — captures frames with OpenCV and analyses them
using the Google Gemini 1.5 Flash API for obstacle detection
and spatial context generation.
"""

import base64
import os
import cv2
import google.generativeai as genai
from PIL import Image
import io


GEMINI_PROMPT = (
    "You are a real-time navigation assistant for a visually impaired person. "
    "Analyse the image and describe any obstacles in the immediate path. "
    "For each obstacle, state what it is and its approximate direction and distance, "
    "e.g. 'Chair approximately 2 metres to your left', 'Step down 1 metre ahead'. "
    "If the path is clear, say 'Path is clear'. "
    "Keep the response under 40 words. Do NOT use markdown."
)


class SceneAnalyzer:
    """
    Manages the camera lifecycle and Gemini API calls.

    Usage:
        analyzer = SceneAnalyzer(api_key="YOUR_KEY", camera_index=0)
        analyzer.start()
        description = analyzer.analyze_current_frame()
        obstacles    = analyzer.extract_obstacles(description)
        analyzer.release()
    """

    def __init__(self, api_key: str, camera_index: int = 0):
        self.camera_index = camera_index
        self.last_description: str = ""
        self._cap: cv2.VideoCapture | None = None

        # Configure Gemini
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-2.5-flash")
    # ------------------------------------------------------------------
    # Camera lifecycle
    # ------------------------------------------------------------------
    def start(self) -> bool:
        """Open the camera. Returns True on success."""
        self._cap = cv2.VideoCapture(self.camera_index)
        if not self._cap.isOpened():
            print(f"[SceneAnalyzer] ERROR: Cannot open camera at index {self.camera_index}")
            return False
        print("[SceneAnalyzer] Camera opened successfully.")
        return True

    def release(self) -> None:
        """Release the camera resource."""
        if self._cap and self._cap.isOpened():
            self._cap.release()
            print("[SceneAnalyzer] Camera released.")

    # ------------------------------------------------------------------
    # Frame capture
    # ------------------------------------------------------------------
    def capture_frame(self) -> "cv2.Mat | None":
        """
        Capture one frame from the camera.
        Returns the frame (BGR numpy array) or None if capture fails.
        """
        if not self._cap or not self._cap.isOpened():
            return None

        ret, frame = self._cap.read()
        if not ret or frame is None or frame.size == 0:
            return None

        return frame

    def _is_valid_frame(self, frame) -> bool:
        """Reject frames that are blank or excessively dark."""
        if frame is None:
            return False
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = gray.mean()
        return mean_brightness > 10  # threshold for 'not blank/dark'

    # ------------------------------------------------------------------
    # Scene analysis
    # ------------------------------------------------------------------
    def analyze_current_frame(self) -> str:
        """
        Capture a valid frame and send it to Gemini for analysis.
        Returns the scene description string.
        """
        for attempt in range(3):
            frame = self.capture_frame()
            if frame is not None and self._is_valid_frame(frame):
                description = self._call_gemini(frame)
                self.last_description = description
                return description
            print(f"[SceneAnalyzer] Invalid frame, retrying ({attempt + 1}/3)...")

        return "Unable to capture a valid frame."

    def _call_gemini(self, frame) -> str:
        """
        Encode frame as JPEG, send to Gemini 1.5 Flash, return text response.
        """
        # Convert BGR → RGB, then to JPEG bytes
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        image_bytes = buffer.getvalue()

        image_part = {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_bytes).decode("utf-8"),
        }

        try:
            response = self._model.generate_content([GEMINI_PROMPT, image_part])
            return response.text.strip()
        except Exception as exc:
            print(f"[SceneAnalyzer] Gemini API error: {exc}")
            return "Scene analysis unavailable."

    # ------------------------------------------------------------------
    # Obstacle extraction
    # ------------------------------------------------------------------
    def extract_obstacles(self, description: str) -> list[str]:
        """
        Parse the Gemini description into a list of individual obstacle strings.
        Returns an empty list if the path is clear.
        """
        if not description or "path is clear" in description.lower():
            return []

        # Split on common sentence delimiters
        raw = description.replace(";", ".").split(".")
        obstacles = [s.strip() for s in raw if s.strip() and len(s.strip()) > 5]
        return obstacles
