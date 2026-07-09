from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from maxo.dialogs.api.entities import (
    DIALOG_EVENT_NAME,
    DialogAction,
    DialogUpdateEvent,
    MediaAttachment,
    MediaId,
    Stack,
)
from maxo.dialogs.api.entities.stack import id_to_str
from maxo.dialogs.api.exceptions import DialogStackOverflow, OutdatedIntent
from maxo.enums import AttachmentType, ChatType
from maxo.fsm import State
from maxo.types import Recipient, User

MEDIA_ID = "media-id"
OTHER_MEDIA_ID = "other-media-id"


def test_outdated_intent_stores_stack_id() -> None:
    error = OutdatedIntent("stack", "outdated")

    assert str(error) == "outdated"
    assert error.stack_id == "stack"


def test_media_id_equality() -> None:
    media_id = MediaId(token=MEDIA_ID)

    assert media_id == MediaId(token=MEDIA_ID)
    assert media_id != MediaId(token=OTHER_MEDIA_ID)
    assert media_id != object()


def test_media_attachment_requires_source() -> None:
    with pytest.raises(ValueError, match="Neither url nor path nor media_id"):
        MediaAttachment(AttachmentType.IMAGE)


def test_media_attachment_file_id_alias_and_equality() -> None:
    media_id = MediaId(token=MEDIA_ID)
    attachment = MediaAttachment(
        AttachmentType.IMAGE,
        file_id=media_id,
        use_pipe=True,
        custom="value",
    )

    assert attachment.file_id == media_id
    assert attachment == MediaAttachment(
        AttachmentType.IMAGE,
        media_id=media_id,
        use_pipe=True,
        custom="value",
    )
    assert attachment != MediaAttachment(AttachmentType.VIDEO, media_id=media_id)
    assert attachment != object()


def test_stack_id_helpers_and_default_flag() -> None:
    assert id_to_str(0) == "0"
    assert Stack(_id="").default() is True
    assert Stack(_id="custom").default() is False


def test_stack_overflow() -> None:
    stack = Stack(intents=[str(index) for index in range(100)])

    with pytest.raises(DialogStackOverflow, match="Cannot open more dialogs"):
        stack.push(State(), {})


def test_dialog_update_event_type() -> None:
    event = DialogUpdateEvent(
        user=User(
            user_id=1,
            first_name="User",
            is_bot=False,
            last_activity_time=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1, chat_id=1),
        action=DialogAction.UPDATE,
        data={"key": "value"},
        intent_id="intent",
        stack_id="stack",
        bot=AsyncMock(),
    )

    assert event.event_type == DIALOG_EVENT_NAME
