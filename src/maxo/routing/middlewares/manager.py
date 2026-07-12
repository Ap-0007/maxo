from collections.abc import Awaitable, Callable, MutableSequence
from typing import Any, Generic, TypeVar, cast

from maxo.routing.ctx import Ctx
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.routing.middlewares.state import (
    EmptyMiddlewareManagerState,
    MiddlewareManagerState,
)
from maxo.types.base import BaseUpdate

_ReturnT = TypeVar("_ReturnT")
_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)
_MiddlewareT = TypeVar("_MiddlewareT", bound=BaseMiddleware[Any])


def _partial_middleware(
    middleware: BaseMiddleware[_UpdateT],
    next: NextMiddleware[_UpdateT],
) -> NextMiddleware[_UpdateT]:
    async def wrapper(ctx: Ctx) -> Any:
        return await middleware(ctx["update"], ctx, next)

    return wrapper


class MiddlewareManager(Generic[_UpdateT]):
    middlewares: MutableSequence[BaseMiddleware[_UpdateT]]
    state: MiddlewareManagerState

    __slots__ = ("middlewares", "state")

    def __init__(self) -> None:
        self.middlewares = []
        self.state = EmptyMiddlewareManagerState()

    def __call__(self, *middlewares: BaseMiddleware[_UpdateT]) -> None:
        self.add(*middlewares)

    def add(self, *middlewares: BaseMiddleware[_UpdateT]) -> None:
        self.state.ensure_add_middleware()
        self.middlewares.extend(middlewares)

    # Подражание aiogram: `dp.message.middleware.register(MyMiddleware())`
    def register(self, middleware: _MiddlewareT) -> _MiddlewareT:
        """Зарегистрировать мидлварь и вернуть ее же."""
        self.add(middleware)
        return middleware

    # Подражание aiogram: `dp.message.middleware.unregister(MyMiddleware())`
    def unregister(self, middleware: BaseMiddleware[_UpdateT]) -> None:
        """Убрать мидлварь. Бросает `ValueError`, если она не зарегистрирована."""
        self.state.ensure_add_middleware()
        self.middlewares.remove(middleware)

    def wrap_middlewares(
        self,
        trigger: Callable[[Ctx], Awaitable[_ReturnT]],
    ) -> NextMiddleware[_UpdateT]:
        middleware = cast(NextMiddleware[_UpdateT], trigger)

        for m in reversed(self.middlewares):
            middleware = _partial_middleware(m, middleware)

        return middleware


class MiddlewareManagerFacade(Generic[_UpdateT]):
    _inner: MiddlewareManager[_UpdateT]
    _outer: MiddlewareManager[_UpdateT]

    __slots__ = ("_inner", "_outer")

    def __init__(self) -> None:
        self._inner = MiddlewareManager()
        self._outer = MiddlewareManager()

    @property
    def inner(self) -> MiddlewareManager[_UpdateT]:
        return self._inner

    @property
    def outer(self) -> MiddlewareManager[_UpdateT]:
        return self._outer

    # Подражание aiogram,
    # чтобы по `router.message_created.middleware(MyMiddleware())`
    # он добавлялся в inner-мидлвари
    def __call__(self, *middlewares: BaseMiddleware[_UpdateT]) -> None:
        self.inner.add(*middlewares)

    # Подражание aiogram,
    # чтобы `router.message_created.middleware.register(MyMiddleware())`
    # добавлял в inner-мидлвари
    def register(self, middleware: _MiddlewareT) -> _MiddlewareT:
        """Зарегистрировать inner-мидлварь и вернуть ее же."""
        return self.inner.register(middleware)

    def unregister(self, middleware: BaseMiddleware[_UpdateT]) -> None:
        """Убрать inner-мидлварь."""
        self.inner.unregister(middleware)
