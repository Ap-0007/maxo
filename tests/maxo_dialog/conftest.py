from datetime import UTC, datetime

from maxo.enums import ChatType
from maxo.routing.updates import MessageCreated
from maxo.types import Message, MessageBody, Recipient, User

NOW = datetime(2026, 1, 1, tzinfo=UTC)


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
