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
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import Back, Cancel, Next, Start
from maxo.dialogs.widgets.text import Const, Format
from maxo.fsm import State, StatesGroup
from maxo.types import Message


class MainSG(StatesGroup):
    start = State()
    next = State()


class SecondarySG(StatesGroup):
    start = State()


async def start(message: Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


async def _is_start(event: object, *_: object) -> bool:
    message = getattr(event, "message", event)
    body = getattr(message, "body", None)
    return getattr(body, "text", None) == "/start"


@pytest.fixture
def message_manager() -> MockMessageManager:
    return MockMessageManager()


@pytest.fixture
def client(dp) -> BotClient:
    return BotClient(dp)


@pytest.fixture
def dp(message_manager: MockMessageManager):
    dp = Dispatcher(storage=JsonMemoryStorage())
    dp.message.register(start, _is_start)

    dp.include_router(
        Dialog(
            Window(
                Const("First"),
                Next(),
                Start(Const("Start"), state=SecondarySG.start, id="start"),
                Cancel(),
                state=MainSG.start,
            ),
            Window(
                Const("Second"),
                Back(),
                state=MainSG.next,
            ),
        ),
    )
    dp.include_router(
        Dialog(
            Window(
                Format("Subdialog"),
                Cancel(),
                state=SecondarySG.start,
            ),
        ),
    )
    setup_dialogs(dp, message_manager=message_manager)
    return dp


async def test_start(dp, message_manager, client):
    # start
    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "First"
    assert first_message.reply_markup


async def test_next_back(dp, message_manager, client):
    await client.send("/start")
    first_message = message_manager.one_message()

    # click next
    message_manager.reset_history()
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Next"),
    )
    message_manager.assert_answered(callback_id)
    second_message = message_manager.one_message()
    assert second_message.body.text == "Second"

    # click back
    message_manager.reset_history()
    callback_id = await client.click(
        second_message,
        InlineButtonTextLocator("Back"),
    )
    message_manager.assert_answered(callback_id)
    last_message = message_manager.one_message()
    assert last_message.body.text == "First"
    assert last_message.reply_markup


async def test_finish_last(dp, message_manager, client):
    await client.send("/start")
    first_message = message_manager.one_message()

    # click back
    message_manager.reset_history()
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Cancel"),
    )
    message_manager.assert_answered(callback_id)
    last_message = message_manager.one_message()
    assert not last_message.reply_markup, "Keyboard closed"


async def test_reset_stack(dp, message_manager, client):
    for _ in range(200):
        message_manager.reset_history()
        await client.send("/start")
        first_message = message_manager.one_message()
        assert first_message.body.text == "First"

    message_manager.reset_history()
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Cancel"),
    )
    message_manager.assert_answered(callback_id)
    last_message = message_manager.one_message()
    assert not last_message.reply_markup, "Keyboard closed"


async def test_subdialog(dp, message_manager, client):
    await client.send("/start")
    first_message = message_manager.one_message()

    # start subdialog
    message_manager.reset_history()
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Start"),
    )
    message_manager.assert_answered(callback_id)
    second_message = message_manager.one_message()
    assert second_message.body.text == "Subdialog"

    # close subdialog
    message_manager.reset_history()
    callback_id = await client.click(
        second_message,
        InlineButtonTextLocator("Cancel"),
    )
    message_manager.assert_answered(callback_id)
    last_message = message_manager.one_message()
    assert last_message.body.text == "First"
    assert last_message.reply_markup
