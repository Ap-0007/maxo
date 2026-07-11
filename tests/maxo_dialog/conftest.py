import asyncio
import time
from typing import Any

import pytest

from maxo.dialogs.api.entities import Context
from maxo.dialogs.test_tools import MockMessageManager
from maxo.enums import ChatType
from maxo.fsm.state import State
from maxo.types import Message, MessageBody, MessageCreated, Recipient, User
from tests.constants import NOW

WidgetData = dict[str, dict[Any, Any] | list[Any] | int | str | float | None]


@pytest.fixture
def message_manager() -> MockMessageManager:
    return MockMessageManager()


async def wait_for_messages(
    message_manager: MockMessageManager,
    count: int = 1,
    timeout: float = 5.0,
) -> None:
    """
    Ждёт, пока фоновая задача отрисует окно.

    `BgManager` кидает обновление через `asyncio.create_task`, поэтому после
    `client.send(...)` сообщение появляется не сразу. Опрос вместо
    `asyncio.sleep(0.1)`: не зависит от скорости машины и не тормозит прогон.
    """
    deadline = time.monotonic() + timeout
    while len(message_manager.sent_messages) < count:
        if time.monotonic() >= deadline:
            msg = (
                f"Фоновая задача не отправила {count} сообщений за {timeout} c, "
                f"получено {len(message_manager.sent_messages)}"
            )
            raise AssertionError(msg)
        await asyncio.sleep(0)


def make_user(user_id: int = 1) -> User:
    return User(
        user_id=user_id,
        is_bot=False,
        first_name="U",
        last_activity_time=NOW,
    )


def make_message_created(text: str = "hi") -> MessageCreated:
    return MessageCreated(
        timestamp=NOW,
        message=Message(
            timestamp=NOW,
            sender=make_user(),
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=10, user_id=1),
            body=MessageBody(mid="m", seq=1, text=text),
        ),
    )


class DummyManager:
    def __init__(
        self,
        preview: bool = False,
        middleware_data: dict[str, Any] | None = None,
        widget_data: WidgetData | None = None,
    ) -> None:
        self._preview = preview
        self.middleware_data = middleware_data or {}
        self.widget_data: WidgetData = {} if widget_data is None else widget_data

    def is_preview(self) -> bool:
        return self._preview

    def current_context(self) -> Context:
        return Context(
            dialog_data={},
            start_data={},
            widget_data=self.widget_data,
            state=State(),
            _stack_id="_stack_id",
            _intent_id="_intent_id",
        )
