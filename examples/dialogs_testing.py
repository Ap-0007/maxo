"""Демонстрация maxo.dialogs.test_tools.

Запуск: python examples/dialogs_testing.py
Не требует токена бота или базы данных.
"""

import asyncio

from maxo import Dispatcher
from maxo.dialogs import Dialog, DialogManager, StartMode, Window, setup_dialogs
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import Back, Button
from maxo.dialogs.widgets.text import Const
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.types import CallbackButton, MessageCallback, MessageCreated


class MenuSG(StatesGroup):
    main = State()
    detail = State()


async def on_detail(
    callback: MessageCallback,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(MenuSG.detail)


async def start_handler(
    message: MessageCreated,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.start(MenuSG.main, mode=StartMode.RESET_STACK)


def make_dialog() -> Dialog:
    return Dialog(
        Window(
            Const("Главное меню"),
            Button(Const("Подробнее"), id="detail", on_click=on_detail),
            state=MenuSG.main,
        ),
        Window(
            Const("Детальная страница"),
            Back(),
            state=MenuSG.detail,
        ),
    )


def make_env() -> tuple[Dispatcher, BotClient, MockMessageManager]:
    storage = JsonMemoryStorage()
    message_manager = MockMessageManager()
    key_builder = DefaultKeyBuilder(with_destiny=True)
    event_isolation = SimpleEventIsolation(key_builder=key_builder)

    test_dp = Dispatcher(
        storage=storage,
        events_isolation=event_isolation,
        key_builder=key_builder,
    )
    test_dp.message_created.handler(start_handler, CommandStart())
    test_dp.include(make_dialog())
    setup_dialogs(
        test_dp,
        message_manager=message_manager,
        events_isolation=event_isolation,
    )

    client = BotClient(test_dp)
    return test_dp, client, message_manager


async def startup(dp: Dispatcher, client: BotClient) -> None:
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)


async def demo_render_window() -> None:
    test_dp, client, message_manager = make_env()
    await startup(test_dp, client)

    await client.send("/start")

    message = message_manager.last_message()
    if message.body.text != "Главное меню":
        raise AssertionError(f"Unexpected text: {message.body.text!r}")
    if message.body.keyboard is None:
        raise AssertionError("Keyboard is missing")
    buttons = [
        btn.text
        for row in message.body.keyboard.buttons
        for btn in row
        if isinstance(btn, CallbackButton)
    ]
    if "Подробнее" not in buttons:
        raise AssertionError(f"Button not found, got: {buttons}")

    print("demo_render_window: OK")


async def demo_render_transition() -> None:
    test_dp, client, message_manager = make_env()
    await startup(test_dp, client)

    await client.send("/start")
    menu_message = message_manager.last_message()
    message_manager.reset_history()

    callback_id = await client.click(menu_message, InlineButtonTextLocator("Подробнее"))
    message_manager.assert_answered(callback_id)

    detail_msg = message_manager.last_message()
    if detail_msg.body.text != "Детальная страница":
        raise AssertionError(f"Unexpected text: {detail_msg.body.text!r}")

    print("demo_render_transition: OK")


async def main() -> None:
    await demo_render_window()
    await demo_render_transition()
    print("All demos passed.")


if __name__ == "__main__":
    asyncio.run(main())
