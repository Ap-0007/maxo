import asyncio
import logging
import os
from typing import Any

from maxo import Bot, Ctx, Dispatcher, flags
from maxo.enums import SenderAction
from maxo.routing.filters import Command
from maxo.routing.flags import get_flag
from maxo.routing.interfaces import BaseMiddleware, NextMiddleware
from maxo.types import MessageCreated
from maxo.utils.chat_action import ChatActionMiddleware

dp = Dispatcher()


# Флаги - это маркеры на хендлерах. Сам хендлер про них ничего не знает,
# читают их мидлвари и утилиты через `get_flag`, `extract_flags` и `check_flags`
class RateLimitMiddleware(BaseMiddleware[MessageCreated]):
    def __init__(self) -> None:
        self._last_call: dict[int, float] = {}

    async def __call__(
        self,
        update: MessageCreated,
        ctx: Ctx,
        next: NextMiddleware[MessageCreated],
    ) -> Any:
        # Хендлеры без флага `rate_limit` не ограничиваются
        rate_limit = get_flag(ctx, "rate_limit")
        if rate_limit is None:
            return await next(ctx)

        user_id = update.message.unsafe_sender.user_id
        now = asyncio.get_running_loop().time()
        if now - self._last_call.get(user_id, 0) < rate_limit:
            await update.answer(text="Слишком часто, подожди немного")
            return None

        self._last_call[user_id] = now
        return await next(ctx)


# Обе мидлвари - inner: флаги хендлера доступны только после выбора хендлера
dp.message_created.middleware(RateLimitMiddleware())
dp.message_created.middleware(ChatActionMiddleware())


# Флаг через декоратор: значение по умолчанию - True
@dp.message_created(Command("typing"))
@flags.chat_action
async def typing_handler(update: MessageCreated) -> None:
    await asyncio.sleep(3)
    await update.answer(text="Всё это время бот «набирал сообщение»")


# Флаг со значением: меняем только тип действия
@dp.message_created(Command("photo"))
@flags.chat_action(SenderAction.SENDING_PHOTO)
async def photo_handler(update: MessageCreated) -> None:
    await asyncio.sleep(3)
    await update.answer(text="А тут бот «отправлял фото»")


# Флаг с именованными аргументами: настраиваем отправщик целиком
@dp.message_created(Command("file"))
@flags.chat_action(action="sending_file", interval=3, initial_sleep=1)
async def file_handler(update: MessageCreated) -> None:
    await asyncio.sleep(5)
    await update.answer(text="Действие ушло не сразу и повторялось раз в 3 секунды")


# Флаги можно задать и при регистрации хендлера, без декоратора
@dp.message_created(Command("limited"), flags={"rate_limit": 5})
async def limited_handler(update: MessageCreated) -> None:
    await update.answer(text="Эту команду можно звать раз в 5 секунд")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(os.environ["TOKEN"])
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
