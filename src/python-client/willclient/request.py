from __future__ import annotations

from typing import Any

import aiohttp
from config import BASE_URL
from .cache import _cache_base

class _Requester:
    def __init__(self):
        self._data = {}
        self._closed: bool=True

    @property
    def token(self) -> str | None:
        return _cache_base.token

    @property
    def closed(self) -> bool:
        return self._closed

    def _cleanup(self):
        _cache_base.session = None
        self._data.clear()
        self._closed = True

    async def _request(self, method: str, path: str, session: aiohttp.ClientSession, **kwargs) -> tuple[aiohttp.ClientResponse, Any]:
        response = await session.request(method, f"{BASE_URL}{path}", timeout=5, **kwargs)
        try:
            body = await response.json()
        except ValueError:
            body = await response.text()
            
        return response, body

    async def post(self, path: str, **kwargs) -> tuple[aiohttp.ClientResponse, Any]:
        return await self._request(
            "POST",
            path=path,
            session=_cache_base.session,
            **kwargs
        )

    async def get(self, path: str, **kwargs) -> tuple[aiohttp.ClientResponse, Any]:
        return await self._request(
            "GET",
            path=path,
            session=_cache_base.session,
            **kwargs
        )

    async def put(self, path: str, **kwargs) -> tuple[aiohttp.ClientResponse, Any]:
        return await self._request(
            "PUT",
            path=path,
            session=_cache_base.session,
            **kwargs
        )

    async def delete(self, path: str, **kwargs) -> tuple[aiohttp.ClientResponse, Any]:
        return await self._request(
            "DELETE",
            path=path,
            session=_cache_base.session,
            **kwargs
        )

    async def close(self):
        if isinstance(_cache_base.session, aiohttp.ClientSession) and not _cache_base.session.closed:
            await _cache_base.session.close()

        self._cleanup()

    async def login(self, email: str, password: str) -> tuple[dict, str | None]:
        resp, login_body = await self._request(
            "POST",
            "/auth/login",
            _cache_base.session,
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
        _cache_base.token = token
        return self._data, token

    async def health(self) -> bool:
        try:
            resp, body = await self._request("GET", "/health", _cache_base.session)
            if resp.status == 200:
                return True
            return False
        except Exception as exc:
            return False


RequestManager = _Requester()