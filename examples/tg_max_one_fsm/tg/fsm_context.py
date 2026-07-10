from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import (
    DEFAULT_DESTINY,
    BaseEventIsolation,
    BaseStorage,
    StorageKey,
)
from aiogram.types import TelegramObject

from ..user_repo import DbUser


class SharedFSMContextMiddleware(BaseMiddleware):
    def __init__(
        self,
        storage: BaseStorage,
        events_isolation: BaseEventIsolation,
    ) -> None:
        self.storage = storage
        self.events_isolation = events_isolation

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["fsm_storage"] = self.storage

        current_user: DbUser | None = data.get("current_user")
        if current_user is None:
            return await handler(event, data)

        context = self.get_context(current_user)
        async with self.events_isolation.lock(key=context.key):
            data.update({"state": context, "raw_state": await context.get_state()})
            return await handler(event, data)

    def get_context(
        self,
        user: DbUser,
    ) -> FSMContext:
        return FSMContext(
            storage=self.storage,
            key=StorageKey(
                user_id=user.shared_id,
                chat_id=user.shared_id,
                bot_id=None,
                thread_id=None,
                business_connection_id=None,
                destiny=DEFAULT_DESTINY,
            ),
        )

    async def close(self) -> None:
        await self.storage.close()
        await self.events_isolation.close()
