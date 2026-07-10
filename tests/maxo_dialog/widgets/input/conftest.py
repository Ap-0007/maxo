"""Shared fixtures and helpers for input widget tests."""

from datetime import UTC, datetime
from typing import cast
from unittest.mock import MagicMock, Mock

from maxo import Ctx
from maxo.dialogs.api.protocols import DialogManager, DialogProtocol
from maxo.enums import AttachmentType, ChatType
from maxo.routing.updates import MessageCreated
from maxo.types import Message, MessageBody, PhotoAttachment, Recipient
from maxo.types.photo_attachment_payload import PhotoAttachmentPayload


def create_text_message(text: str) -> MessageCreated:
    """Create a text message for testing."""
    return MessageCreated(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        message=Message(
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
            body=MessageBody(mid="test_mid", seq=1, text=text),
        ),
    )


def create_photo_message() -> MessageCreated:
    """Create a photo message for testing."""
    photo = PhotoAttachment(
        type=AttachmentType.IMAGE,
        payload=PhotoAttachmentPayload(
            photo_id=123,
            token="test_token",  # noqa: S106
            url="https://example.com/photo.jpg",
        ),
    )
    return MessageCreated(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        message=Message(
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
            body=MessageBody(mid="test_mid", seq=1, text=None, attachments=[photo]),
        ),
    )


def create_message_no_body() -> MessageCreated:
    """Create a message without body for testing."""
    return MessageCreated(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        message=Message(
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
            # cast нужен, чтобы проверить runtime-ветку TextInput для body=None.
            body=cast(MessageBody, None),
        ),
    )


def setup_mock_manager(
    mock_manager: DialogManager,
    event: MessageCreated | None = None,
) -> None:
    """Set up mock manager with middleware_data and optional event."""
    manager_mock = cast(MagicMock, mock_manager)
    manager_mock.middleware_data = {"ctx": {}}
    if event:
        manager_mock.event = event


def dialog_protocol() -> DialogProtocol:
    # cast нужен, чтобы не создавать полноценный Dialog для input widget тестов.
    return cast(DialogProtocol, Mock())


def empty_ctx() -> Ctx:
    return Ctx({})
