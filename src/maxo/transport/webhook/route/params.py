from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, TypeAlias

from maxo.transport.webhook.engines.target import Target

RouteParams: TypeAlias = Mapping[str, Any]


class RouteParam(Protocol):
    async def build(self, target: Target, params: RouteParams) -> str:
        """
        Build raw path param value for an outgoing URL.

        Route will encode this value for URL path.
        """

    async def parse(self, value: str, params: RouteParams) -> Any:
        """Parse incoming framework path param into a normalized route param value."""


@dataclass(frozen=True, slots=True)
class RouteParamBinding:
    name: str
    param: RouteParam


class BotIdParam(RouteParam):
    async def build(self, target: Target, params: RouteParams) -> str:
        if target.bot_id is None:
            raise ValueError(
                "Cannot build bot_id route param: target.bot_id is not resolved yet.",
            )
        return str(target.bot_id)

    async def parse(self, value: str, params: RouteParams) -> int:
        return int(value)


class BotTokenParam(RouteParam):
    async def build(self, target: Target, params: RouteParams) -> str:
        return target.bot_token

    async def parse(self, value: str, params: RouteParams) -> str:
        return value
