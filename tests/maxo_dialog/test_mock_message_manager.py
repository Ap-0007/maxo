from unittest.mock import MagicMock

from maxo.dialogs.api.entities import ShowMode
from maxo.dialogs.api.entities.new_message import OldMessage, UnknownText
from maxo.dialogs.test_tools.mock_message_manager import MockMessageManager
from maxo.enums import ChatType
from maxo.types import Recipient


def make_old_message(text: str | None | UnknownText) -> OldMessage:
    return OldMessage(
        recipient=Recipient(chat_type=ChatType.CHAT, chat_id=1, user_id=2),
        message_id="mid-1",
        sequence_id=0,
        text=text,
        attachments=[],
    )


async def test_remove_kbd_keeps_text() -> None:
    manager = MockMessageManager()

    await manager.remove_kbd(MagicMock(), ShowMode.EDIT, make_old_message("hello"))

    assert manager.one_message().body.text == "hello"


async def test_remove_kbd_maps_unknown_text_to_none() -> None:
    # `_get_last_message` отдаёт UnknownText.UNKNOWN, когда сообщение
    # восстановлено из стека - в MessageBody.text он попасть не должен
    manager = MockMessageManager()

    await manager.remove_kbd(
        MagicMock(),
        ShowMode.EDIT,
        make_old_message(UnknownText.UNKNOWN),
    )

    assert manager.one_message().body.text is None
