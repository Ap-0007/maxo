from datetime import UTC, datetime

import pytest

from maxo.enums import ChatType
from maxo.routing.ctx import Ctx
from maxo.routing.filters import SyncFilter
from maxo.routing.updates.message_created import MessageCreated
from maxo.types import Message, MessageBody, Recipient, User


def _update() -> MessageCreated:
    return MessageCreated(
        message=Message(
            body=MessageBody(mid="test", seq=1),
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
            timestamp=datetime.now(UTC),
            sender=User(
                user_id=1,
                first_name="Test",
                is_bot=False,
                last_activity_time=datetime.now(UTC),
            ),
        ),
        timestamp=datetime.now(UTC),
    )


async def test_sync_filter_returns_true() -> None:
    f: SyncFilter[MessageCreated] = SyncFilter(lambda _: True)
    assert await f(_update(), Ctx({})) is True


async def test_sync_filter_returns_false() -> None:
    f: SyncFilter[MessageCreated] = SyncFilter(lambda _: False)
    assert await f(_update(), Ctx({})) is False


async def test_sync_filter_checks_field() -> None:
    f: SyncFilter[MessageCreated] = SyncFilter(lambda u: u.message is not None)
    assert await f(_update(), Ctx({})) is True


async def test_sync_filter_composes_with_and() -> None:
    f = SyncFilter[MessageCreated](lambda _: True) & SyncFilter[MessageCreated](
        lambda _: False,
    )
    assert await f(_update(), Ctx({})) is False


def _boom(_: MessageCreated) -> bool:
    raise ValueError("boom")


async def test_sync_filter_exceptions_as_false() -> None:
    f: SyncFilter[MessageCreated] = SyncFilter(_boom, exceptions_as_false=True)
    assert await f(_update(), Ctx({})) is False


async def test_sync_filter_reraises_by_default() -> None:
    f: SyncFilter[MessageCreated] = SyncFilter(_boom)
    with pytest.raises(ValueError, match="boom"):
        await f(_update(), Ctx({}))


async def test_sync_filter_run_in_thread() -> None:
    f: SyncFilter[MessageCreated] = SyncFilter(
        lambda u: u.message is not None,
        run_in_thread=True,
    )
    assert await f(_update(), Ctx({})) is True
