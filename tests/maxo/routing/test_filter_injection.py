from typing import Any

from maxo import Bot, Ctx
from maxo.enums import ChatType
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.filters import BaseFilter
from maxo.routing.filters.filter_object import FilterObject
from maxo.routing.sentinels import UNHANDLED
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


class PlainFilter(BaseFilter[Any]):
    async def __call__(self, update: Any, ctx: Ctx) -> bool:
        return True


class NamedParamsFilter(BaseFilter[Any]):
    """Фильтр с необязательными зависимостями: их может не быть в контексте."""

    def __init__(self) -> None:
        self.seen: dict[str, Any] = {}

    async def __call__(
        self,
        update: Any,
        ctx: Ctx,
        bot: Bot | None = None,
        answer: str | None = None,
    ) -> bool:
        self.seen = {"bot": bot, "answer": answer}
        return True


class RequiredParamsFilter(BaseFilter[Any]):
    """Фильтр с обязательной зависимостью: протокол `Filter` это разрешает."""

    def __init__(self) -> None:
        self.seen: dict[str, Any] = {}

    async def __call__(self, update: Any, ctx: Ctx, bot: Bot) -> bool:
        self.seen = {"bot": bot}
        return True


class VarKwargsFilter(BaseFilter[Any]):
    def __init__(self) -> None:
        self.seen: dict[str, Any] = {}

    async def __call__(self, update: Any, ctx: Ctx, **kwargs: Any) -> bool:
        self.seen = kwargs
        return True


async def test_plain_filter_is_called_without_extras() -> None:
    filter_ = PlainFilter()

    assert await FilterObject(filter_)(None, Ctx({"bot": "BOT"})) is True


async def test_named_params_are_injected_from_ctx() -> None:
    filter_ = NamedParamsFilter()
    ctx = Ctx({"bot": "BOT", "answer": 42, "unused": "no"})

    assert await FilterObject(filter_)(None, ctx) is True
    assert filter_.seen == {"bot": "BOT", "answer": 42}


async def test_missing_params_fall_back_to_defaults() -> None:
    filter_ = NamedParamsFilter()

    assert await FilterObject(filter_)(None, Ctx({})) is True
    assert filter_.seen == {"bot": None, "answer": None}


async def test_varkwargs_filter_receives_whole_ctx_without_reserved() -> None:
    filter_ = VarKwargsFilter()
    ctx = Ctx({"bot": "BOT", "update": "UPD", "ctx": "CTX", "extra": 1})

    assert await FilterObject(filter_)(None, ctx) is True
    assert filter_.seen == {"bot": "BOT", "extra": 1}


async def test_injection_works_inside_logic_filters() -> None:
    first = NamedParamsFilter()
    second = NamedParamsFilter()
    combined = first & second
    ctx = Ctx({"answer": "yes"})

    assert await combined(None, ctx) is True
    assert first.seen["answer"] == "yes"
    assert second.seen["answer"] == "yes"


async def test_injection_in_handler_filter() -> None:
    dp = Dispatcher()
    filter_ = NamedParamsFilter()
    bot = make_bot()

    @dp.message_created(filter_)
    async def handler(update: MessageCreated) -> str:
        return "ok"

    result = await dp.feed_update(make_update(), bot)

    assert result == "ok"
    assert filter_.seen["bot"] is bot


async def test_injection_in_observer_filter() -> None:
    dp = Dispatcher()
    filter_ = NamedParamsFilter()
    dp.message_created.filter(filter_)
    bot = make_bot()

    @dp.message_created()
    async def handler(update: MessageCreated) -> str:
        return "ok"

    assert await dp.feed_update(make_update(), bot) == "ok"
    assert filter_.seen["bot"] is bot


async def test_failing_filter_still_skips_handler() -> None:
    class RejectingFilter(BaseFilter[Any]):
        async def __call__(
            self,
            update: Any,
            ctx: Ctx,
            bot: Bot | None = None,
        ) -> bool:
            return bot is None

    dp = Dispatcher()

    @dp.message_created(RejectingFilter())
    async def handler(update: MessageCreated) -> str:
        return "ok"  # pragma: no cover

    assert await dp.feed_update(make_update(), make_bot()) is UNHANDLED


async def test_filter_object_is_callable_like_a_filter() -> None:
    filter_ = NamedParamsFilter()
    wrapped = FilterObject(filter_)
    ctx = Ctx({"answer": "yes"})

    assert await wrapped(None, ctx) is True
    assert filter_.seen["answer"] == "yes"
    assert wrapped.filter is filter_
    assert FilterObject.call is FilterObject.__call__


async def test_filter_object_is_not_wrapped_twice() -> None:
    filter_ = PlainFilter()

    assert FilterObject(FilterObject(filter_)).filter is filter_


def test_filter_object_repr_shows_wrapped_filter() -> None:
    filter_ = PlainFilter()

    assert repr(filter_) in repr(FilterObject(filter_))


async def test_required_param_is_injected() -> None:
    dp = Dispatcher()
    filter_ = RequiredParamsFilter()
    bot = make_bot()

    @dp.message_created(filter_)
    async def handler(update: MessageCreated) -> str:
        return "ok"

    assert await dp.feed_update(make_update(), bot) == "ok"
    assert filter_.seen["bot"] is bot
