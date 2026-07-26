import platform

from unihttp.http import HTTPRequest, HTTPResponse
from unihttp.middlewares import AsyncHandler

from maxo.__meta__ import __version__

USER_AGENT = f"Python/{platform.python_version()} maxo/{__version__}"


class AuthMiddleware:
    __slots__ = ("_token",)

    def __init__(self, token: str) -> None:
        self._token = token

    async def handle(
        self,
        request: HTTPRequest,
        next_handler: AsyncHandler,
    ) -> HTTPResponse:
        request.header.setdefault("Authorization", self._token)
        request.header.setdefault("User-Agent", USER_AGENT)
        return await next_handler(request)
