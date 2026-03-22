"""
safe_stride_app.py
SafeStrideApp — central coordinator.
Ties together SceneAnalyzer, GPSNavigator, TTSEngine,
RouteLogger, and EmergencyAlert according to the flow diagram.
"""

import os
import time
from dotenv import load_dotenv

from scene_analyzer import SceneAnalyzer
from gps_navigator import GPSNavigator
from tts_engine import TTSEngine
from route_logger import RouteLogger
from emergency_alert import EmergencyAlert
from auth_client import AuthClient

load_dotenv()


class SafeStrideApp:
    """
    Mode constants
    """
    MODE_INDOOR = "indoor"
    MODE_OUTDOOR = "outdoor"

    def __init__(self):
        # Config from environment
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8080")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.maps_api_key = os.getenv("MAPS_API_KEY", "")

        # State
        self.is_running: bool = False
        self.current_mode: str = self.MODE_INDOOR
        self.token: str = ""
        self.user: dict = {}

        # Sub-components (initialised in start())
        self.auth_client = AuthClient(self.backend_url)
        self.tts: TTSEngine | None = None
        self.scene_analyzer: SceneAnalyzer | None = None
        self.gps_navigator: GPSNavigator | None = None
        self.route_logger: RouteLogger | None = None
        self.emergency_alert: EmergencyAlert | None = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    def authenticate(self, phone: str, password: str) -> bool:
        """Login with credentials. Returns True on success."""
        token, user = self.auth_client.login(phone, password)
        if token:
            self.token = token
            self.user = user
            return True
        return False

    def register(
        self,
        name: str,
        phone: str,
        password: str,
        emergency_contact: str,
    ) -> bool:
        """Register a new user. Returns True on success."""
        token, user = self.auth_client.register(name, phone, password, emergency_contact)
        if token:
            self.token = token
            self.user = user
            return True
        return False

    def restore_session(self) -> bool:
        """Try to restore a previously saved JWT. Returns True if found."""
        token = self.auth_client.load_saved_session()
        if token:
            self.token = token
            self.user = self.auth_client.user
            return True
        return False

    # ------------------------------------------------------------------
    # Hardware initialisation
    # ------------------------------------------------------------------
    def start(self) -> None:
        """
        Initialise all hardware channels and sub-components.
        Must be called after authentication.
        """
        print("[SafeStrideApp] Initialising hardware...")

        # TTS
        self.tts = TTSEngine(rate=160, volume=1.0)
        self.tts.speak("SafeStride is starting. Welcome.")

        # Camera + Gemini
        self.scene_analyzer = SceneAnalyzer(
            api_key=self.gemini_api_key,
            camera_index=0,
        )
        cam_ok = self.scene_analyzer.start()
        if not cam_ok:
            self.tts.speak("Camera not found. Scene intelligence unavailable.")

        # GPS + Maps
        self.gps_navigator = GPSNavigator(maps_api_key=self.maps_api_key)

        # Route logger + emergency alert
        user_id = self.user.get("userId", 0)
        self.route_logger = RouteLogger(base_url=self.backend_url, token=self.token)
        self.emergency_alert = EmergencyAlert(base_url=self.backend_url, token=self.token)

        self.is_running = True
        print("[SafeStrideApp] All hardware ready.")
        self.tts.speak("Hardware ready. Please select indoor or outdoor mode.")

    def stop(self) -> None:
        """Release all resources and end the session."""
        self.is_running = False
        if self.scene_analyzer:
            self.scene_analyzer.release()
        if self.tts:
            self.tts.stop()
        print("[SafeStrideApp] Session ended. Hardware released.")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self, mode: str = MODE_INDOOR, destination: str = "") -> None:
        """
        Run one full session cycle in the chosen mode.
        Call repeatedly (or in a loop) from the Kivy UI.
        """
        self.current_mode = mode
        user_id = self.user.get("userId", 0)

        if mode == self.MODE_INDOOR:
            self._run_indoor_cycle(user_id)
        else:
            self._run_outdoor_cycle(user_id, destination)

    # ------------------------------------------------------------------
    # Indoor cycle — scene intelligence
    # ------------------------------------------------------------------
    def _run_indoor_cycle(self, user_id: int) -> None:
        print("[SafeStrideApp] Indoor cycle started.")
        description = self.scene_analyzer.analyze_current_frame()
        print(f"[SafeStrideApp] Scene: {description}")

        obstacles = self.scene_analyzer.extract_obstacles(description)

        if obstacles:
            for obs in obstacles:
                self.tts.speak(obs)
                time.sleep(0.5)
        else:
            self.tts.speak("Path is clear.")

        # Log current position
        location = self.gps_navigator.get_location()
        if location:
            lat, lng = location
            self.route_logger.log_route(user_id, lat, lng, label="indoor")
            self.emergency_alert.track_location(user_id, lat, lng)

    # ------------------------------------------------------------------
    # Outdoor cycle — GPS navigation
    # ------------------------------------------------------------------
    def _run_outdoor_cycle(self, user_id: int, destination: str) -> None:
        print(f"[SafeStrideApp] Outdoor cycle: navigating to '{destination}'")

        if not destination:
            self.tts.speak("Please say your destination.")
            return

        self.tts.speak(f"Getting directions to {destination}. Please wait.")
        steps = self.gps_navigator.calc_route(destination)

        if not steps:
            self.tts.speak("Could not fetch directions. Please check your internet connection.")
            return

        location = self.gps_navigator.get_location()
        for i, step in enumerate(steps):
            self.tts.speak_blocking(step)
            # Log waypoint at each step
            if location:
                lat, lng = location
                self.route_logger.log_route(user_id, lat, lng, label=f"step_{i + 1}")
                self.emergency_alert.track_location(user_id, lat, lng)
            time.sleep(0.8)

        self.tts.speak("You have arrived at your destination.")

    # ------------------------------------------------------------------
    # Emergency
    # ------------------------------------------------------------------
    def trigger_sos(self) -> None:
        """Called when user presses SOS button."""
        user_id = self.user.get("userId", 0)
        location = self.gps_navigator.get_location() if self.gps_navigator else None
        lat, lng = location if location else (0.0, 0.0)
        self.emergency_alert.send_alert(user_id, lat, lng)
        self.tts.speak("SOS alert sent to your emergency contact.")

    # ------------------------------------------------------------------
    # Mode switching
    # ------------------------------------------------------------------
    def process_frame(self) -> str:
        """Public shortcut: capture and analyse a frame (indoor)."""
        return self.scene_analyzer.analyze_current_frame()

    def navigate(self, destination: str) -> list[str]:
        """Public shortcut: get route steps (outdoor)."""
        return self.gps_navigator.calc_route(destination)
