import asyncio
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
from maxo.dialogs.api.entities import GROUP_STACK_ID, AccessSettings
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import Button
from maxo.dialogs.widgets.text import Const, Format
from maxo.fsm import State, StatesGroup


class MainSG(StatesGroup):
    start = State()


window = Window(
    Format("stub"),
    Button(Const("Button"), id="btn"),
    state=MainSG.start,
)


async def start(event: Any, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


async def start_shared(event: Any, dialog_manager: DialogManager) -> None:
    dialog_manager = dialog_manager.bg(stack_id=GROUP_STACK_ID)
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


async def add_shared(event: Any, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(
        MainSG.start,
        access_settings=AccessSettings(
            user_ids=[1, 2],
        ),
    )


async def _is_start(event: object, *_: object) -> bool:
    message = getattr(event, "message", event)
    body = getattr(message, "body", None)
    return getattr(body, "text", None) == "/start"


async def _is_add(event: object, *_: object) -> bool:
    message = getattr(event, "message", event)
    body = getattr(message, "body", None)
    return getattr(body, "text", None) == "/add"


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
    return BotClient(dp, chat_id=-1, user_id=1, chat_type="group")


@pytest.fixture
def second_client(dp):
    return BotClient(dp, chat_id=-1, user_id=2, chat_type="group")


async def test_second_user(dp, client, second_client, message_manager):
    dp.message.register(start, _is_start)
    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"
    message_manager.reset_history()
    await second_client.send("test")
    assert not message_manager.sent_messages
    await second_client.click(
        first_message,
        InlineButtonTextLocator("Button"),
    )
    assert not message_manager.sent_messages


async def test_change_settings(dp, client, second_client, message_manager):
    dp.message.register(start, _is_start)
    dp.message.register(add_shared, _is_add)

    await client.send("/start")
    message_manager.reset_history()

    await client.send("/add")
    window_message = message_manager.one_message()
    message_manager.reset_history()

    await second_client.click(
        window_message,
        InlineButtonTextLocator("Button"),
    )
    window_message = message_manager.one_message()
    message_manager.reset_history()
    assert window_message.body.text == "stub"

    await client.send("/start")
    window_message = message_manager.one_message()
    message_manager.reset_history()

    await second_client.click(
        window_message,
        InlineButtonTextLocator("Button"),
    )
    assert not message_manager.sent_messages


async def test_change_settings_bg(dp, client, second_client, message_manager):
    dp.message.register(start, _is_start)
    dp.message.register(add_shared, _is_add)

    await client.send("/start")
    message_manager.reset_history()

    await client.send("/add")
    window_message = message_manager.one_message()
    message_manager.reset_history()

    await second_client.click(
        window_message,
        InlineButtonTextLocator("Button"),
    )
    window_message = message_manager.one_message()
    message_manager.reset_history()
    assert window_message.body.text == "stub"

    await client.send("/start")
    window_message = message_manager.one_message()
    message_manager.reset_history()

    await second_client.click(
        window_message,
        InlineButtonTextLocator("Button"),
    )
    assert not message_manager.sent_messages


async def test_same_user(dp, client, message_manager):
    dp.message.register(start, _is_start)
    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"
    message_manager.reset_history()
    await client.send("test")
    assert not message_manager.sent_messages  # no resend
    await client.click(
        first_message,
        InlineButtonTextLocator("Button"),
    )
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"


async def test_shared_stack(dp, client, second_client, message_manager):
    dp.message.register(start_shared, _is_start)
    await client.send("/start")
    await asyncio.sleep(0.02)  # synchronization workaround, fixme

    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"
    message_manager.reset_history()
    await second_client.send("test")
    assert not message_manager.sent_messages
    await second_client.click(
        first_message,
        InlineButtonTextLocator("Button"),
    )
    second_message = message_manager.one_message()
    assert second_message.body.text == "stub"
