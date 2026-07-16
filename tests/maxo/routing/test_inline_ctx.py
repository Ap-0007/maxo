from maxo import Bot, Ctx
from maxo.enums import ChatType
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.filters import BaseFilter
from maxo.routing.utils import inline_ctx
from maxo.types import Message, MessageBody, MessageCreated, Recipient, User
from tests.constants import NOW
from tests.factories import make_bot


def make_update() -> MessageCreated:
    return MessageCreated(
        message=Message(
            body=MessageBody(mid="test", seq=1, text="hi"),
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
            timestamp=NOW,
            sender=User(
                user_id=1,
                first_name="Test",
                is_bot=False,
                last_activity_time=NOW,
            ),
        ),
        timestamp=NOW,
    )


class ContextFilter(BaseFilter[MessageCreated]):
    def __init__(self) -> None:
        self.bot: Bot | None = None
        self.answer: str | None = None

    @inline_ctx
    async def __call__(
        self,
        update: MessageCreated,
        ctx: Ctx,
        bot: Bot,
        answer: str | None = None,
    ) -> bool:
        self.bot = bot
        self.answer = answer
        return True


async def test_inline_ctx_expands_context_in_filter() -> None:
    filter_ = ContextFilter()
    bot = make_bot()

    assert await filter_(make_update(), Ctx({"bot": bot, "answer": "yes"})) is True
    assert filter_.bot is bot
    assert filter_.answer == "yes"


async def test_inline_ctx_works_in_handler_filter() -> None:
    dp = Dispatcher()
    filter_ = ContextFilter()
    bot = make_bot()

    @dp.message_created(filter_)
    async def handler(update: MessageCreated) -> str:
        return "ok"

    assert await dp.feed_update(make_update(), bot) == "ok"
    assert filter_.bot is bot
