import re
from abc import ABC, abstractmethod
from hmac import compare_digest
from typing import Final

from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.web.base import WebRequest

SECRET_TOKEN_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{5,256}$")
SECRET_TOKEN_HEADER: Final[str] = "x-max-bot-api-secret"  # noqa: S105


class SecretToken(ABC):
    """Base class for secret token verification in webhook requests."""

    async def verify(
        self,
        request: WebRequest,
        route_params: RouteParams,
    ) -> bool:
        """
        Verify the incoming secret token from the request.

        :param request: The webhook request object.
        :param route_params: Route parameters mapping.
        :return: True if the token is valid, False otherwise.
        """
        incoming_secret_token = request.headers.get(SECRET_TOKEN_HEADER)
        if incoming_secret_token is None:
            return False
        bot_token = route_params.get("bot_token")
        return compare_digest(
            incoming_secret_token,
            await self.secret_token(
                bot_token=bot_token if isinstance(bot_token, str) else None,
            ),
        )

    @abstractmethod
    async def secret_token(self, bot_token: str | None) -> str:
        """
        Return the webhook secret token associated with the given bot token.

        :param bot_token: The bot token identifying the target bot, or None if
            the route does not expose one (e.g. not yet resolved, or single-bot route).
        :return: The secret token string for this bot.
        """
        raise NotImplementedError


class StaticSecretToken(SecretToken):
    """
    Static secret token implementation for webhook security.

    Token format: 5-256 characters, only `^[a-zA-Z0-9_-]{5,256}$` are allowed.
    See: https://dev.max.ru/docs-api/methods/POST/subscriptions
    """

    def __init__(self, secret_token: str) -> None:
        if not SECRET_TOKEN_PATTERN.match(secret_token):
            raise ValueError(
                "Invalid secret token format. "
                "Must be 5-256 characters, only ^[a-zA-Z0-9_-]{5,256}$.",
            )
        self.__secret_token = secret_token

    async def secret_token(self, bot_token: str | None) -> str:
        """
        Return the static secret token.

        :param bot_token: Unused for static tokens.
        :return: The configured secret token.
        """
        return self.__secret_token
