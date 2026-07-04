from maxo import Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.widgets.media.static import StaticMedia
from maxo.fsm import State, StatesGroup
from maxo.fsm.storages.memory import MemoryStorage
from maxo.types import Message


class MainSG(StatesGroup):
    with_url = State()
    with_path = State()


dialog = Dialog(
    Window(
        StaticMedia(url="fake_image.png"),
        state=MainSG.with_url,
    ),
    Window(
        StaticMedia(path="fake_image.png"),
        state=MainSG.with_path,
    ),
)


async def start_url(message: Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.with_url, mode=StartMode.RESET_STACK)


async def start_path(message: Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.with_path, mode=StartMode.RESET_STACK)


async def _is_url(event: object, *_: object) -> bool:
    message = getattr(event, "message", event)
    body = getattr(message, "body", None)
    return getattr(body, "text", None) == "/url"


async def _is_path(event: object, *_: object) -> bool:
    message = getattr(event, "message", event)
    body = getattr(message, "body", None)
    return getattr(body, "text", None) == "/path"


async def test_click():
    dp = Dispatcher(
        storage=MemoryStorage(),
    )
    dp.include_router(dialog)
    dp.message.register(start_url, _is_url)
    dp.message.register(start_path, _is_path)

    client = BotClient(dp)
    message_manager = MockMessageManager()
    setup_dialogs(dp, message_manager=message_manager)

    # with url parameter
    await client.send("/url")
    first_message = message_manager.one_message()
    assert first_message.photo

    message_manager.reset_history()

    # with path parameter
    await client.send("/path")
    first_message = message_manager.one_message()
    assert first_message.photo
