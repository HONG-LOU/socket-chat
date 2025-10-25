from typing import Any, Dict, Optional

import httpx


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self._client = httpx.Client(base_url=self.base_url, timeout=10.0)

    def set_token(self, token: Optional[str]) -> None:
        self.token = token

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def register(self, email: str, password: str, display_name: str) -> Dict[str, Any]:
        res = self._client.post(
            "/api/auth/register",
            headers=self._headers(),
            json={"email": email, "password": password, "display_name": display_name},
        )
        res.raise_for_status()
        return res.json()

    def login(self, email: str, password: str) -> str:
        res = self._client.post(
            "/api/auth/login",
            headers=self._headers(),
            json={"email": email, "password": password},
        )
        res.raise_for_status()
        token = res.json()["access_token"]
        self.set_token(token)
        return token

    def me(self) -> Dict[str, Any]:
        res = self._client.get("/api/me", headers=self._headers())
        res.raise_for_status()
        return res.json()

    def friends(self) -> list[Dict[str, Any]]:
        res = self._client.get("/api/friends", headers=self._headers())
        res.raise_for_status()
        return res.json()

    def add_friend(self, friend_email: str) -> Dict[str, Any]:
        res = self._client.post(
            "/api/friends/add",
            headers=self._headers(),
            json={"friend_email": friend_email},
        )
        res.raise_for_status()
        return res.json()

    def history(self, friend_id: int) -> list[Dict[str, Any]]:
        res = self._client.get(f"/api/messages/{friend_id}", headers=self._headers())
        res.raise_for_status()
        return res.json()
