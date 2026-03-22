"""
gps_navigator.py
GPSNavigator — fetches the device's current GPS coordinates via geopy
and retrieves step-by-step walking directions from the Google Maps
Directions API.
"""

import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


MAPS_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"


class GPSNavigator:
    """
    Manages GPS location retrieval and route calculation.

    Usage:
        nav = GPSNavigator(maps_api_key="YOUR_KEY")
        lat, lng = nav.get_location()
        steps = nav.get_directions(lat, lng, "Central Park, New York")
        for step in steps:
            print(step)   # e.g. "Turn left in 50 metres onto Main Street"
    """

    def __init__(self, maps_api_key: str):
        self.maps_api_key = maps_api_key
        self.current_lat: float | None = None
        self.current_lng: float | None = None
        self.destination: str = ""
        self._geolocator = Nominatim(user_agent="safestride_app")

    # ------------------------------------------------------------------
    # Location
    # ------------------------------------------------------------------
    def get_location(self) -> tuple[float, float] | None:
        """
        Retrieve the device's current GPS coordinates.
        On a real device this uses the hardware GPS chip; here we use
        Nominatim reverse-geocoding as a fallback for testing.

        Returns (latitude, longitude) or None if unavailable.
        """
        # --- Real device integration point ---
        # On Android via Plyer: from plyer import gps; gps.start(...)
        # For desktop/testing, attempt to resolve via IP-based location
        try:
            ip_resp = requests.get("https://ipinfo.io/json", timeout=5)
            if ip_resp.status_code == 200:
                data = ip_resp.json()
                loc = data.get("loc", "")
                if loc:
                    lat, lng = map(float, loc.split(","))
                    self.current_lat = lat
                    self.current_lng = lng
                    print(f"[GPSNavigator] Location: {lat}, {lng}")
                    return lat, lng
        except Exception as exc:
            print(f"[GPSNavigator] IP location failed: {exc}")

        return None

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    def get_directions(
        self,
        origin_lat: float,
        origin_lng: float,
        destination: str,
    ) -> list[str]:
        """
        Call the Google Maps Directions API and return a list of plain-text
        step-by-step walking instructions.

        Each item looks like: "Turn left onto MG Road (200 m)"
        """
        self.destination = destination

        params = {
            "origin": f"{origin_lat},{origin_lng}",
            "destination": destination,
            "mode": "walking",
            "key": self.maps_api_key,
        }

        try:
            resp = requests.get(MAPS_DIRECTIONS_URL, params=params, timeout=10)
            data = resp.json()
        except Exception as exc:
            print(f"[GPSNavigator] Maps API request failed: {exc}")
            return []

        if data.get("status") != "OK":
            print(f"[GPSNavigator] Maps API error: {data.get('status')}")
            return []

        steps: list[str] = []
        for leg in data["routes"][0]["legs"]:
            for step in leg["steps"]:
                instruction = self._strip_html(step.get("html_instructions", ""))
                distance = step["distance"]["text"]
                steps.append(f"{instruction} ({distance})")

        print(f"[GPSNavigator] {len(steps)} route steps fetched.")
        return steps

    def calc_route(
        self,
        destination: str,
    ) -> list[str]:
        """
        Convenience method: fetch location first, then get directions.
        """
        location = self.get_location()
        if not location:
            return ["GPS signal unavailable. Please try again."]
        lat, lng = location
        return self.get_directions(lat, lng, destination)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from Maps API instruction strings."""
        import re
        clean = re.sub(r"<[^>]+>", " ", text)
        return " ".join(clean.split())
