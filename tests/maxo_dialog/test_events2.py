from typing import Any

import pytest

from maxo import Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.text import Format
from maxo.fsm import State, StatesGroup


class MainSG(StatesGroup):
    start = State()


window = Window(
    Format("stub"),
    state=MainSG.start,
)


async def start(event: Any, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


async def _is_start(event: object, *_: object) -> bool:
    message = getattr(event, "message", event)
    body = getattr(message, "body", None)
    return getattr(body, "text", None) == "/start"


@pytest.fixture
def message_manager():
    return MockMessageManager()


@pytest.fixture
def dp(message_manager):
    dp = Dispatcher(storage=JsonMemoryStorage())
    dp.include_router(Dialog(window))
    setup_dialogs(dp, message_manager=message_manager)
    return dp


@pytest.fixture
def client(dp):
    return BotClient(dp)


async def test_click(dp, client, message_manager):
    dp.message.register(start, _is_start)
    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"


async def test_request_join(dp, client, message_manager):
    dp.user_added_to_chat.register(start, _is_start)
    await client.user_added_to_chat()
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"


async def test_my_chat_member_update(dp, client, message_manager):
    dp.bot_added_to_chat.register(start, _is_start)
    await client.bot_added_to_chat()
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"
