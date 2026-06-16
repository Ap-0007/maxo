from typing import Any
from unittest.mock import MagicMock

from maxo import Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import ConfirmButton
from maxo.dialogs.widgets.text import Const
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.routing.updates import MessageCallback, MessageCreated


class MainSG(StatesGroup):
    main = State()


async def on_pizza(
    callback: MessageCallback,
    _: Any,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.middleware_data["on_pizza"](callback.id)


async def on_pizza_cancel(
    callback: MessageCallback,
    _: Any,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.middleware_data["on_pizza_cancel"](callback.id)


async def on_sushi(
    callback: MessageCallback,
    _: Any,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.middleware_data["on_sushi"](callback.id)


confirm_dialog = Dialog(
    Window(
        Const("Нажми на любой заказ"),
        ConfirmButton(
            primary_text=Const("Заказать пиццу"),
            confirm_text=Const("Точно"),
            cancel_text=Const("Передумал"),
            warning_text=Const("Подтверди заказ пиццы"),
            on_confirm=on_pizza,
            on_cancel=on_pizza_cancel,
            id="pizza",
        ),
        ConfirmButton(
            primary_text=Const("Заказать суши"),
            confirm_text=Const("Точно суши"),
            cancel_text=Const("Передумал, не суши"),
            warning_text=None,
            on_confirm=on_sushi,
            on_cancel=None,
            id="sushi",
        ),
        state=MainSG.main,
    ),
)


async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.main, mode=StartMode.RESET_STACK)


async def test_click() -> None:
    on_pizza_mock = MagicMock()
    on_pizza_cancel_mock = MagicMock()
    on_sushi_mock = MagicMock()

    key_builder = DefaultKeyBuilder(with_destiny=True)
    event_isolation = SimpleEventIsolation(key_builder=key_builder)
    dp = Dispatcher(
        storage=JsonMemoryStorage(),
        events_isolation=event_isolation,
        key_builder=key_builder,
        workflow_data={
            "on_pizza": on_pizza_mock,
            "on_pizza_cancel": on_pizza_cancel_mock,
            "on_sushi": on_sushi_mock,
        },
    )
    dp.include(confirm_dialog)
    dp.message_created.handler(start, CommandStart())

    client = BotClient(dp)
    message_manager = MockMessageManager()
    setup_dialogs(dp, message_manager=message_manager, events_isolation=event_isolation)

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    dialog_message = message_manager.one_message()
    assert dialog_message.body.text == "Нажми на любой заказ"
    assert len(dialog_message.body.reply_markup.buttons) == 2
    assert len(dialog_message.body.reply_markup.buttons[0]) == 1
    assert len(dialog_message.body.reply_markup.buttons[1]) == 1

    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("Заказать пиццу"))
    dialog_message = message_manager.one_message()
    assert len(dialog_message.body.reply_markup.buttons) == 3
    assert len(dialog_message.body.reply_markup.buttons[0]) == 1
    assert len(dialog_message.body.reply_markup.buttons[1]) == 2
    assert len(dialog_message.body.reply_markup.buttons[2]) == 1

    message_manager.reset_history()
    cancel_id = await client.click(dialog_message, InlineButtonTextLocator("Передумал"))
    on_pizza_cancel_mock.assert_called_once_with(cancel_id)
    dialog_message = message_manager.one_message()
    assert len(dialog_message.body.reply_markup.buttons) == 2
    assert len(dialog_message.body.reply_markup.buttons[0]) == 1
    assert len(dialog_message.body.reply_markup.buttons[1]) == 1

    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("Заказать пиццу"))
    dialog_message = message_manager.one_message()
    assert len(dialog_message.body.reply_markup.buttons) == 3
    assert len(dialog_message.body.reply_markup.buttons[0]) == 1
    assert len(dialog_message.body.reply_markup.buttons[1]) == 2
    assert len(dialog_message.body.reply_markup.buttons[2]) == 1

    message_manager.reset_history()
    confirm_id = await client.click(dialog_message, InlineButtonTextLocator("Точно"))
    on_pizza_mock.assert_called_once_with(confirm_id)
    dialog_message = message_manager.one_message()
    assert len(dialog_message.body.reply_markup.buttons) == 2
    assert len(dialog_message.body.reply_markup.buttons[0]) == 1
    assert len(dialog_message.body.reply_markup.buttons[1]) == 1

    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("Заказать суши"))
    dialog_message = message_manager.one_message()
    assert len(dialog_message.body.reply_markup.buttons) == 2
    assert len(dialog_message.body.reply_markup.buttons[0]) == 1
    assert len(dialog_message.body.reply_markup.buttons[1]) == 2

    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("Передумал, не суши"))
    dialog_message = message_manager.one_message()
    assert len(dialog_message.body.reply_markup.buttons) == 2
    assert len(dialog_message.body.reply_markup.buttons[0]) == 1
    assert len(dialog_message.body.reply_markup.buttons[1]) == 1

    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("Заказать суши"))
    dialog_message = message_manager.one_message()
    assert len(dialog_message.body.reply_markup.buttons) == 2
    assert len(dialog_message.body.reply_markup.buttons[0]) == 1
    assert len(dialog_message.body.reply_markup.buttons[1]) == 2

    message_manager.reset_history()
    confirm_id = await client.click(
        dialog_message,
        InlineButtonTextLocator("Точно суши"),
    )
    on_sushi_mock.assert_called_once_with(confirm_id)
    dialog_message = message_manager.one_message()
    assert len(dialog_message.body.reply_markup.buttons) == 2
    assert len(dialog_message.body.reply_markup.buttons[0]) == 1
    assert len(dialog_message.body.reply_markup.buttons[1]) == 1
