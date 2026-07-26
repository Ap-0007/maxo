"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/utils/chat_action.py.

Original code licensed under MIT by aiogram contributors

The MIT License (MIT)

Copyright (c) 2017 - present Alex Root Junior

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
"""

import asyncio
import time
from asyncio import Event, Lock
from collections.abc import Mapping
from contextlib import suppress
from types import TracebackType
from typing import Any, Final, Self

from maxo import Bot, loggers
from maxo.enums.sender_action import SenderAction
from maxo.routing.ctx import Ctx
from maxo.routing.flags import get_flag
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.routing.middlewares.update_context import UPDATE_CONTEXT_KEY
from maxo.types import MessageCallback, MessageCreated, MessageEdited
from maxo.types.base import BaseUpdate

DEFAULT_INTERVAL: Final = 5.0
DEFAULT_INITIAL_SLEEP: Final = 0.0
CHAT_ACTION_KEY: Final = "chat_action"


class ChatActionSender:
    """
    Шлёт действие бота в чат, пока выполняется долгая операция.

    MAX показывает действие («бот набирает сообщение», «бот отправляет фото»)
    ограниченное время, поэтому его надо переотправлять. Отправкой занимается
    фоновая задача, которая живёт, пока открыт асинхронный контекстный менеджер:

    ```python
    async with ChatActionSender.typing_on(bot=bot, chat_id=chat_id):
        result = await do_something_long()
    await update.answer(text=result)
    ```
    """

    __slots__ = (
        "_close_event",
        "_closed_event",
        "_lock",
        "_task",
        "action",
        "bot",
        "chat_id",
        "initial_sleep",
        "interval",
    )

    def __init__(
        self,
        *,
        bot: Bot,
        chat_id: int,
        action: SenderAction | str = SenderAction.TYPING_ON,
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> None:
        """
        Создаёт отправщик действий, не запуская его.

        Args:
            bot: экземпляр бота.
            chat_id: ID чата, в который шлётся действие.
            action: тип действия.
            interval: интервал между отправками в секундах.
            initial_sleep: задержка перед первой отправкой в секундах.

        """
        self.bot = bot
        self.chat_id = chat_id
        self.action = SenderAction(action)
        self.interval = interval
        self.initial_sleep = initial_sleep

        self._lock = Lock()
        self._close_event = Event()
        self._closed_event = Event()
        self._task: asyncio.Task[Any] | None = None

    @property
    def running(self) -> bool:
        """Фоновая задача отправки действий запущена."""
        return bool(self._task)

    async def _wait(self, interval: float) -> None:
        with suppress(TimeoutError):
            await asyncio.wait_for(self._close_event.wait(), interval)

    async def _worker(self) -> None:
        loggers.utils.debug(
            "Запущена отправка действия %r в chat_id=%s",
            self.action,
            self.chat_id,
        )
        try:
            counter = 0
            await self._wait(self.initial_sleep)
            while not self._close_event.is_set():
                start = time.monotonic()
                loggers.utils.debug(
                    "Отправлено действие %r в chat_id=%s (уже отправлено %d)",
                    self.action,
                    self.chat_id,
                    counter,
                )
                await self.bot.send_action(chat_id=self.chat_id, action=self.action)
                counter += 1

                await self._wait(self.interval - (time.monotonic() - start))
        finally:
            loggers.utils.debug(
                "Остановлена отправка действия %r в chat_id=%s",
                self.action,
                self.chat_id,
            )
            self._closed_event.set()

    async def _run(self) -> None:
        async with self._lock:
            self._close_event.clear()
            self._closed_event.clear()
            if self.running:
                raise RuntimeError("Отправка действий уже запущена")
            self._task = asyncio.create_task(self._worker())

    async def _stop(self) -> None:
        async with self._lock:
            if not self.running:
                return
            if not self._close_event.is_set():  # pragma: no branch
                self._close_event.set()
                await self._closed_event.wait()
            self._task = None

    async def __aenter__(self) -> Self:
        await self._run()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._stop()

    @classmethod
    def _factory(
        cls,
        action: SenderAction,
        chat_id: int,
        bot: Bot,
        interval: float,
        initial_sleep: float,
    ) -> "ChatActionSender":
        return cls(
            bot=bot,
            chat_id=chat_id,
            action=action,
            interval=interval,
            initial_sleep=initial_sleep,
        )

    @classmethod
    def typing_on(
        cls,
        chat_id: int,
        bot: Bot,
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        """Отправщик действия «бот набирает сообщение»."""
        return cls._factory(
            SenderAction.TYPING_ON,
            chat_id,
            bot,
            interval,
            initial_sleep,
        )

    @classmethod
    def sending_photo(
        cls,
        chat_id: int,
        bot: Bot,
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        """Отправщик действия «бот отправляет фото»."""
        return cls._factory(
            SenderAction.SENDING_PHOTO,
            chat_id,
            bot,
            interval,
            initial_sleep,
        )

    @classmethod
    def sending_video(
        cls,
        chat_id: int,
        bot: Bot,
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        """Отправщик действия «бот отправляет видео»."""
        return cls._factory(
            SenderAction.SENDING_VIDEO,
            chat_id,
            bot,
            interval,
            initial_sleep,
        )

    @classmethod
    def sending_audio(
        cls,
        chat_id: int,
        bot: Bot,
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        """Отправщик действия «бот отправляет аудиофайл»."""
        return cls._factory(
            SenderAction.SENDING_AUDIO,
            chat_id,
            bot,
            interval,
            initial_sleep,
        )

    @classmethod
    def sending_file(
        cls,
        chat_id: int,
        bot: Bot,
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        """Отправщик действия «бот отправляет файл»."""
        return cls._factory(
            SenderAction.SENDING_FILE,
            chat_id,
            bot,
            interval,
            initial_sleep,
        )

    @classmethod
    def mark_seen(
        cls,
        chat_id: int,
        bot: Bot,
        interval: float = DEFAULT_INTERVAL,
        initial_sleep: float = DEFAULT_INITIAL_SLEEP,
    ) -> "ChatActionSender":
        """Отправщик действия «бот прочитал сообщения»."""
        return cls._factory(
            SenderAction.MARK_SEEN,
            chat_id,
            bot,
            interval,
            initial_sleep,
        )


class ChatActionMiddleware(BaseMiddleware[BaseUpdate]):
    """
    Inner-мидлварь: шлёт действие бота, пока работает хендлер.

    Подключается к нужному обсёрверу:

    ```python
    dp.message_created.middleware(ChatActionMiddleware())
    ```

    По умолчанию шлёт `typing_on`. Поведение конкретного хендлера настраивается
    флагом `chat_action`: строкой/`SenderAction` меняется только тип действия,
    именованными аргументами - вся конфигурация отправщика.
    """

    __slots__ = ()

    async def __call__(
        self,
        update: BaseUpdate,
        ctx: Ctx,
        next: NextMiddleware[BaseUpdate],
    ) -> Any:
        chat_id = self._resolve_chat_id(update, ctx)
        bot = ctx.get("bot")
        if chat_id is None or bot is None:
            return await next(ctx)

        kwargs = self._resolve_sender_kwargs(ctx)
        async with ChatActionSender(bot=bot, chat_id=chat_id, **kwargs):
            return await next(ctx)

    def _resolve_chat_id(self, update: BaseUpdate, ctx: Ctx) -> int | None:
        update_context = ctx.get(UPDATE_CONTEXT_KEY)
        if update_context is not None and update_context.chat_id is not None:
            return int(update_context.chat_id)

        if isinstance(update, (MessageCreated, MessageEdited)):
            return update.message.recipient.chat_id
        if isinstance(update, MessageCallback) and update.message is not None:
            return update.message.recipient.chat_id
        return None

    def _resolve_sender_kwargs(self, ctx: Ctx) -> dict[str, Any]:
        chat_action = get_flag(ctx, CHAT_ACTION_KEY) or SenderAction.TYPING_ON

        if isinstance(chat_action, bool):
            return {"action": SenderAction.TYPING_ON}
        if not isinstance(chat_action, Mapping):
            return {"action": SenderAction(chat_action)}

        kwargs: dict[str, Any] = {}
        for key in ("action", "interval", "initial_sleep"):
            value = chat_action.get(key)
            if value is not None:
                kwargs[key] = value
        return kwargs
