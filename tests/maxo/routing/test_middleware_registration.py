from typing import Any

import pytest

from maxo.errors.state import StateError
from maxo.routing.ctx import Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.interfaces import BaseMiddleware, NextMiddleware
from maxo.routing.middlewares.state import StartedMiddlewareManagerState


class NoopMiddleware(BaseMiddleware[Any]):
    async def __call__(
        self,
        update: Any,
        ctx: Ctx,
        next: NextMiddleware[Any],
    ) -> Any:
        return await next(ctx)


def test_register_adds_inner_and_returns_middleware() -> None:
    dp = Dispatcher()
    middleware = NoopMiddleware()

    returned = dp.message_created.middleware.register(middleware)

    assert returned is middleware
    assert list(dp.message_created.middleware.inner.middlewares) == [middleware]


def test_outer_register_adds_outer_and_returns_middleware() -> None:
    dp = Dispatcher()
    middleware = NoopMiddleware()

    returned = dp.message_created.outer_middleware.register(middleware)

    assert returned is middleware
    assert list(dp.message_created.middleware.outer.middlewares) == [middleware]


def test_unregister_removes_inner_middleware() -> None:
    dp = Dispatcher()
    middleware = NoopMiddleware()
    dp.message_created.middleware.register(middleware)

    dp.message_created.middleware.unregister(middleware)

    assert list(dp.message_created.middleware.inner.middlewares) == []


def test_unregister_removes_outer_middleware() -> None:
    dp = Dispatcher()
    middleware = NoopMiddleware()
    dp.message_created.outer_middleware.register(middleware)

    dp.message_created.outer_middleware.unregister(middleware)

    assert list(dp.message_created.middleware.outer.middlewares) == []


def test_unregister_unknown_middleware_raises() -> None:
    dp = Dispatcher()

    with pytest.raises(ValueError):  # noqa: PT011
        dp.message_created.middleware.unregister(NoopMiddleware())


def test_call_without_arguments_returns_inner_decorator() -> None:
    dp = Dispatcher()
    middleware = NoopMiddleware()

    returned = dp.message_created.middleware()(middleware)

    assert returned is middleware
    assert list(dp.message_created.middleware.inner.middlewares) == [middleware]


def test_call_without_arguments_returns_outer_decorator() -> None:
    dp = Dispatcher()
    middleware = NoopMiddleware()

    returned = dp.message_created.outer_middleware()(middleware)

    assert returned is middleware
    assert list(dp.message_created.middleware.outer.middlewares) == [middleware]


def test_unregister_after_startup_reports_removal() -> None:
    dp = Dispatcher()
    middleware = NoopMiddleware()
    dp.message_created.middleware.register(middleware)

    dp.message_created.middleware.inner.state = StartedMiddlewareManagerState()

    with pytest.raises(StateError, match="Can't remove middleware after startup"):
        dp.message_created.middleware.unregister(middleware)
