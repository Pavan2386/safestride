"""
emergency_alert.py
EmergencyAlert — sends an SOS notification with live GPS
coordinates to the registered caregiver via the Spring Boot backend.
"""

import requests


class EmergencyAlert:
    """
    Triggers emergency notifications through the Spring Boot REST API.

    Usage:
        alert = EmergencyAlert(base_url="http://localhost:8080", token="JWT...")
        alert.send_alert(user_id=1, lat=17.385, lng=78.486)
    """

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.contact_number: str = ""
        self.message: str = "SOS! I need help."
        self.is_triggered: bool = False
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def send_alert(
        self,
        user_id: int,
        lat: float,
        lng: float,
        message: str | None = None,
    ) -> bool:
        """
        POST an SOS alert to /api/emergency/alert.
        Spring Boot will SMS the registered emergencyContact with location.
        Returns True if the alert was dispatched successfully.
        """
        payload = {
            "userId": user_id,
            "latitude": lat,
            "longitude": lng,
            "message": message or self.message,
            "mapsLink": f"https://maps.google.com/?q={lat},{lng}",
        }

        try:
            resp = requests.post(
                f"{self.base_url}/api/emergency/alert",
                json=payload,
                headers=self._headers,
                timeout=8,
            )
            if resp.status_code == 200:
                self.is_triggered = True
                print(f"[EmergencyAlert] SOS sent for user {user_id} at {lat},{lng}")
                return True
            print(f"[EmergencyAlert] Alert failed: {resp.status_code} {resp.text}")
            return False
        except Exception as exc:
            print(f"[EmergencyAlert] Network error: {exc}")
            return False

    def track_location(
        self,
        user_id: int,
        lat: float,
        lng: float,
    ) -> bool:
        """
        POST the current GPS coordinates to the real-time tracking endpoint
        so the caregiver portal can display the live position.
        """
        payload = {"userId": user_id, "latitude": lat, "longitude": lng}
        try:
            resp = requests.post(
                f"{self.base_url}/api/tracking/update",
                json=payload,
                headers=self._headers,
                timeout=5,
            )
            return resp.status_code == 200
        except Exception as exc:
            print(f"[EmergencyAlert] Tracking update error: {exc}")
            return False

    def notify_contact(self, user_id: int) -> bool:
        """
        Ask the Spring Boot backend to resend the last SOS to the caregiver.
        """
        try:
            resp = requests.post(
                f"{self.base_url}/api/emergency/notify/{user_id}",
                headers=self._headers,
                timeout=8,
            )
            return resp.status_code == 200
        except Exception as exc:
            print(f"[EmergencyAlert] Notify error: {exc}")
            return False

    def reset(self) -> None:
        """Clear the triggered flag after the emergency is resolved."""
        self.is_triggered = False
