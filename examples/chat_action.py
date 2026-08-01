import asyncio
import logging
import os

from maxo import Bot, Dispatcher
from maxo.routing.filters import Command
from maxo.types import MessageCreated
from maxo.utils.chat_action import ChatActionSender

bot = Bot(os.environ["TOKEN"])
dp = Dispatcher()


# Без мидлвари отправщик действий используется как контекстный менеджер:
# пока внутри выполняется долгая работа, MAX показывает «бот набирает сообщение»
@dp.message_created(Command("report"))
async def report_handler(update: MessageCreated, bot: Bot) -> None:
    async with ChatActionSender.typing_on(bot=bot, chat_id=update.chat_id):
        await asyncio.sleep(10)  # долгая работа: поход в БД, генерация отчёта и т.п.

    await update.answer(text="Отчёт готов")


# Тип действия выбирается под задачу: тут бот «отправляет файл»
@dp.message_created(Command("file"))
async def file_handler(update: MessageCreated, bot: Bot) -> None:
    async with ChatActionSender.sending_file(
        bot=bot,
        chat_id=update.chat_id,
        initial_sleep=1,  # не мигать действием, если работа окажется быстрой
    ):
        await asyncio.sleep(10)

    await update.answer(text="Файл собран")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
