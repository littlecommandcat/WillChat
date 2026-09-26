from typing import Any

import aiohttp
from config import BASE_URL

class Requester:
    def __init__(self):
        self._session: aiohttp.ClientSession | None=None
        self._data = {}
        self._token: str | None=None
        self._closed: bool=True
        # self._init_session()

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def closed(self) -> bool:
        return self._closed

    def _init_session(self) -> None:
        self._closed = False
        if isinstance(self._session, aiohttp.ClientSession) and not self._session.closed:
            return
        
        self._session = aiohttp.ClientSession()
        # return self._session

    def _cleanup(self):
        self._session = None
        self._data.clear()
        self._closed = True

    async def _request(self, method: str, path: str, session: aiohttp.ClientSession, **kwargs) -> tuple[aiohttp.ClientResponse, Any]:
        response = await session.request(method, f"{BASE_URL}{path}", timeout=5, **kwargs)
        try:
            body = await response.json()
        except ValueError:
            body = await response.text()
        # data = body.get("data", {}) if isinstance(body, dict) else body
        # print("status:", response.status)
        # print("data:", body)
        return response, body

    async def post(self, path: str, **kwargs) -> tuple[aiohttp.ClientResponse, Any]:
        return await self._request(
            "POST",
            path=path,
            session=self._session,
            **kwargs
        )

    async def get(self, path: str, **kwargs) -> tuple[aiohttp.ClientResponse, Any]:
        return await self._request(
            "GET",
            path=path,
            session=self._session,
            **kwargs
        )

    async def put(self, path: str, **kwargs) -> tuple[aiohttp.ClientResponse, Any]:
        return await self._request(
            "PUT",
            path=path,
            session=self._session,
            **kwargs
        )

    async def delete(self, path: str, **kwargs) -> tuple[aiohttp.ClientResponse, Any]:
        return await self._request(
            "DELETE",
            path=path,
            session=self._session,
            **kwargs
        )

    async def close(self):
        if isinstance(self._session, aiohttp.ClientSession) and not self._session.closed:
            await self._session.close()

        self._cleanup()

    async def login(self, email: str, password: str) -> tuple[dict, str | None]:
        # self._init_session()
        resp, login_body = await self._request(
            "POST",
            "/auth/login",
            self._session,
            json={
                "email": email,
                "password": password,
            },
        )

        if resp.status not in [200, 201]:
            return {}, None

        token = (
            login_body.get("data", {}).get("token", "")
            if isinstance(login_body, dict)
            else ""
        )
        self._data = login_body.get("data", {})
        self._token = token
        return self._data, token