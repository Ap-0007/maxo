from typing import cast
from unittest.mock import MagicMock, Mock

from maxo import Ctx
from maxo.dialogs.api.protocols import DialogManager, DialogProtocol
from maxo.enums import AttachmentType, ChatType
from maxo.routing.updates import MessageCreated
from maxo.types import Message, MessageBody, PhotoAttachment, Recipient
from maxo.types.photo_attachment_payload import PhotoAttachmentPayload
from tests.constants import NOW


def create_text_message(text: str) -> MessageCreated:
    return MessageCreated(
        timestamp=NOW,
        message=Message(
            timestamp=NOW,
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
            body=MessageBody(mid="test_mid", seq=1, text=text),
        ),
    )


def create_photo_message() -> MessageCreated:
    photo = PhotoAttachment(
        type=AttachmentType.IMAGE,
        payload=PhotoAttachmentPayload(
            photo_id=123,
            token="test_token",  # noqa: S106
            url="https://example.com/photo.jpg",
        ),
    )
    return MessageCreated(
        timestamp=NOW,
        message=Message(
            timestamp=NOW,
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
            body=MessageBody(mid="test_mid", seq=1, text=None, attachments=[photo]),
        ),
    )


def create_message_no_body() -> MessageCreated:
    return MessageCreated(
        timestamp=NOW,
        message=Message(
            timestamp=NOW,
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
            # cast нужен, чтобы проверить runtime-ветку TextInput для body=None.
            body=cast(MessageBody, None),
        ),
    )


def setup_mock_manager(
    mock_manager: DialogManager,
    event: MessageCreated | None = None,
) -> None:
    manager_mock = cast(MagicMock, mock_manager)
    manager_mock.middleware_data = {"ctx": {}}
    if event:
        manager_mock.event = event


def dialog_protocol() -> DialogProtocol:
    # cast нужен, чтобы не создавать полноценный Dialog для input widget тестов.
    return cast(DialogProtocol, Mock())


def empty_ctx() -> Ctx:
    return Ctx({})
