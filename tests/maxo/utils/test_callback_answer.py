from typing import cast
from unittest.mock import AsyncMock

from maxo.routing.ctx import Ctx
from maxo.routing.updates.message_callback import MessageCallback
from maxo.utils.callback_answer import (
    CALLBACK_ANSWER_KEY,
    CallbackAnswerMiddleware,
)


async def _next_ok(ctx: Ctx) -> str:
    return "OK"


async def test_answers_after_handler_by_default() -> None:
    update = AsyncMock()
    mw = CallbackAnswerMiddleware()
    result = await mw(cast(MessageCallback, update), Ctx({}), _next_ok)
    assert result == "OK"
    update.answer.assert_awaited_once_with()


async def test_before_answers_before_handler() -> None:
    order: list[str] = []
    update = AsyncMock()
    update.answer = AsyncMock(side_effect=lambda **_: order.append("answer"))

    async def next_fn(ctx: Ctx) -> str:
        order.append("handler")
        return "OK"

    mw = CallbackAnswerMiddleware(before=True)
    await mw(cast(MessageCallback, update), Ctx({}), next_fn)
    assert order == ["answer", "handler"]


async def test_handler_can_disable() -> None:
    update = AsyncMock()

    async def next_fn(ctx: Ctx) -> str:
        ctx[CALLBACK_ANSWER_KEY].disabled = True
        return "OK"

    mw = CallbackAnswerMiddleware()
    await mw(cast(MessageCallback, update), Ctx({}), next_fn)
    update.answer.assert_not_awaited()


async def test_handler_can_change_notification() -> None:
    update = AsyncMock()

    async def next_fn(ctx: Ctx) -> str:
        ctx[CALLBACK_ANSWER_KEY].notification = "done"
        return "OK"

    mw = CallbackAnswerMiddleware()
    await mw(cast(MessageCallback, update), Ctx({}), next_fn)
    update.answer.assert_awaited_once_with(notification="done")


async def test_no_double_answer_when_before() -> None:
    update = AsyncMock()
    mw = CallbackAnswerMiddleware(before=True)
    await mw(cast(MessageCallback, update), Ctx({}), _next_ok)
    update.answer.assert_awaited_once_with()
