"""
auth_client.py
AuthClient — handles login and registration HTTP calls
to the Spring Boot /api/auth endpoints.
"""

import requests
import json
import os


class AuthClient:
    """
    REST client for authentication against the Spring Boot backend.

    Usage:
        client = AuthClient(base_url="http://localhost:8080")
        token, user = client.login("9876543210", "mypassword")
        token, user = client.register("Alice", "9876543210", "pass", "9000000000")
    """

    TOKEN_FILE = ".safestride_token"

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token: str = ""
        self.user: dict = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register(
        self,
        name: str,
        phone: str,
        password: str,
        emergency_contact: str,
    ) -> tuple[str, dict]:
        """
        POST /api/auth/register
        Returns (jwt_token, user_dict) on success, ("", {}) on failure.
        """
        payload = {
            "name": name,
            "phone": phone,
            "password": password,
            "emergencyContact": emergency_contact,
        }
        try:
            resp = requests.post(
                f"{self.base_url}/api/auth/register",
                json=payload,
                timeout=10,
            )
            if resp.status_code == 201:
                data = resp.json()
                self.token = data.get("token", "")
                self.user = data.get("user", {})
                self._save_token(self.token)
                print(f"[AuthClient] Registered: {name}")
                return self.token, self.user
            print(f"[AuthClient] Register failed: {resp.status_code} {resp.text}")
            return "", {}
        except Exception as exc:
            print(f"[AuthClient] Register error: {exc}")
            return "", {}

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    def login(self, phone: str, password: str) -> tuple[str, dict]:
        """
        POST /api/auth/login
        Returns (jwt_token, user_dict) on success, ("", {}) on failure.
        """
        payload = {"phone": phone, "password": password}
        try:
            resp = requests.post(
                f"{self.base_url}/api/auth/login",
                json=payload,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("token", "")
                self.user = data.get("user", {})
                self._save_token(self.token)
                print(f"[AuthClient] Logged in: {self.user.get('name')}")
                return self.token, self.user
            print(f"[AuthClient] Login failed: {resp.status_code} {resp.text}")
            return "", {}
        except Exception as exc:
            print(f"[AuthClient] Login error: {exc}")
            return "", {}

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------
    def load_saved_session(self) -> str:
        """
        Read a previously saved JWT from disk.
        Returns the token string or "" if none saved.
        """
        if os.path.exists(self.TOKEN_FILE):
            try:
                with open(self.TOKEN_FILE, "r") as f:
                    data = json.load(f)
                    self.token = data.get("token", "")
                    self.user = data.get("user", {})
                    print("[AuthClient] Session restored from disk.")
                    return self.token
            except Exception:
                pass
        return ""

    def _save_token(self, token: str) -> None:
        try:
            with open(self.TOKEN_FILE, "w") as f:
                json.dump({"token": token, "user": self.user}, f)
        except Exception as exc:
            print(f"[AuthClient] Could not save token: {exc}")

    def logout(self) -> None:
        """Clear saved session."""
        self.token = ""
        self.user = {}
        if os.path.exists(self.TOKEN_FILE):
            os.remove(self.TOKEN_FILE)
        print("[AuthClient] Logged out.")
