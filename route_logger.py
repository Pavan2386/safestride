"""
route_logger.py
RouteLogger — sends GPS waypoints to the Spring Boot backend
for persistent storage in MySQL/PostgreSQL.
"""

import requests
from datetime import datetime


class RouteLogger:
    """
    Logs route waypoints to the Spring Boot REST endpoint.

    Usage:
        logger = RouteLogger(base_url="http://localhost:8080", token="JWT...")
        logger.log_route(user_id=1, lat=17.385, lng=78.486, label="outdoor")
        history = logger.get_routes(user_id=1)
    """

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def log_route(
        self,
        user_id: int,
        lat: float,
        lng: float,
        label: str = "waypoint",
    ) -> bool:
        """
        POST a single waypoint to /api/routes/log.
        Returns True on success.
        """
        payload = {
            "userId": user_id,
            "latitude": lat,
            "longitude": lng,
            "label": label,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        try:
            resp = requests.post(
                f"{self.base_url}/api/routes/log",
                json=payload,
                headers=self._headers,
                timeout=5,
            )
            if resp.status_code == 201:
                print(f"[RouteLogger] Waypoint saved: {lat}, {lng}")
                return True
            print(f"[RouteLogger] Save failed: {resp.status_code} {resp.text}")
            return False
        except Exception as exc:
            print(f"[RouteLogger] Network error: {exc}")
            return False

    def save_to_db(self, user_id: int, waypoints: list[dict]) -> bool:
        """
        Bulk save a list of waypoints [{lat, lng, label, timestamp}, ...].
        """
        payload = {"userId": user_id, "waypoints": waypoints}
        try:
            resp = requests.post(
                f"{self.base_url}/api/routes/bulk",
                json=payload,
                headers=self._headers,
                timeout=10,
            )
            return resp.status_code == 201
        except Exception as exc:
            print(f"[RouteLogger] Bulk save error: {exc}")
            return False

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def get_routes(self, user_id: int) -> list[dict]:
        """
        GET all saved routes for a user from /api/routes/{userId}.
        Returns a list of waypoint dicts.
        """
        try:
            resp = requests.get(
                f"{self.base_url}/api/routes/{user_id}",
                headers=self._headers,
                timeout=5,
            )
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as exc:
            print(f"[RouteLogger] Fetch error: {exc}")
            return []
