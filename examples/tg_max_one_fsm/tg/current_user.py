from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.middlewares.user_context import EVENT_CONTEXT_KEY, EventContext
from aiogram.types import TelegramObject

from ..ids import TgId
from ..user_repo import ExternalType, UserRepo


class CurrentUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_repo: UserRepo = data["user_repo"]
        event_context: EventContext = data[EVENT_CONTEXT_KEY]

        if event_context.user_id:
            user = await user_repo.get_or_create_user(
                external_id=TgId(event_context.user_id),
                external_type=ExternalType.TG,
            )
            data["current_user"] = user

        return await handler(event, data)
