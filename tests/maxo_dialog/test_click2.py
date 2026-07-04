from typing import Any
from unittest.mock import Mock

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
from maxo.dialogs.widgets.kbd import Button
from maxo.dialogs.widgets.text import Const, Format
from maxo.fsm import State, StatesGroup
from maxo.types import Message


class MainSG(StatesGroup):
    start = State()
    next = State()


async def on_click(event, button, manager: DialogManager) -> None:
    manager.middleware_data["usecase"]()
    await manager.next()


async def on_finish(event, button, manager: DialogManager) -> None:
    await manager.done()


async def second_getter(user_getter, **kwargs) -> dict[str, Any]:
    return {
        "user": user_getter(),
    }


dialog = Dialog(
    Window(
        Format("stub"),
        Button(Const("Button"), id="hello", on_click=on_click),
        state=MainSG.start,
    ),
    Window(
        Format("Next {user}"),
        Button(Const("Finish"), id="hello", on_click=on_finish),
        state=MainSG.next,
        getter=second_getter,
    ),
)


async def start(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


async def _is_start(event: object, *_: object) -> bool:
    message = getattr(event, "message", event)
    body = getattr(message, "body", None)
    return getattr(body, "text", None) == "/start"


async def test_click():
    usecase = Mock()
    user_getter = Mock(side_effect=["Username"])
    dp = Dispatcher(
        workflow_data={"usecase": usecase, "user_getter": user_getter},
        storage=JsonMemoryStorage(),
    )
    dp.include_router(dialog)
    dp.message.register(start, _is_start)

    client = BotClient(dp)
    message_manager = MockMessageManager()
    setup_dialogs(dp, message_manager=message_manager)

    # start
    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"
    assert first_message.reply_markup
    user_getter.assert_not_called()

    # redraw
    message_manager.reset_history()
    await client.send("whatever")

    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"

    # click next
    message_manager.reset_history()
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Button"),
    )

    message_manager.assert_answered(callback_id)
    usecase.assert_called()
    second_message = message_manager.one_message()
    assert second_message.body.text == "Next Username"
    assert second_message.reply_markup.inline_keyboard
    user_getter.assert_called_once()
