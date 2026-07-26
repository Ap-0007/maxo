from collections.abc import Awaitable, Callable, MutableSequence
from typing import Any, Generic, TypeVar, cast, overload

from maxo.routing.ctx import Ctx
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.routing.middlewares.state import (
    EmptyMiddlewareManagerState,
    MiddlewareManagerState,
)
from maxo.types.base import BaseUpdate

_ReturnT = TypeVar("_ReturnT")
_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)


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

    @overload
    def __call__(
        self,
    ) -> Callable[[BaseMiddleware[_UpdateT]], BaseMiddleware[_UpdateT]]: ...

    @overload
    def __call__(self, *middlewares: BaseMiddleware[_UpdateT]) -> None: ...

    # Подражание aiogram: вызов без аргументов возвращает декоратор,
    # чтобы работал привычный `@router.message_created.outer_middleware()`
    def __call__(
        self,
        *middlewares: BaseMiddleware[_UpdateT],
    ) -> Callable[[BaseMiddleware[_UpdateT]], BaseMiddleware[_UpdateT]] | None:
        if not middlewares:
            return self.register
        self.add(*middlewares)
        return None

    def add(self, *middlewares: BaseMiddleware[_UpdateT]) -> None:
        self.state.ensure_add_middleware()
        self.middlewares.extend(middlewares)

    def register(
        self,
        middleware: BaseMiddleware[_UpdateT],
    ) -> BaseMiddleware[_UpdateT]:
        """Зарегистрировать мидлварь и вернуть ее же."""
        self.add(middleware)
        return middleware

    def unregister(self, middleware: BaseMiddleware[_UpdateT]) -> None:
        """Убрать мидлварь. Бросает `ValueError`, если она не зарегистрирована."""
        self.state.ensure_remove_middleware()
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
    @overload
    def __call__(
        self,
    ) -> Callable[[BaseMiddleware[_UpdateT]], BaseMiddleware[_UpdateT]]: ...

    @overload
    def __call__(self, *middlewares: BaseMiddleware[_UpdateT]) -> None: ...

    def __call__(
        self,
        *middlewares: BaseMiddleware[_UpdateT],
    ) -> Callable[[BaseMiddleware[_UpdateT]], BaseMiddleware[_UpdateT]] | None:
        return self.inner(*middlewares)

    def register(
        self,
        middleware: BaseMiddleware[_UpdateT],
    ) -> BaseMiddleware[_UpdateT]:
        """Зарегистрировать inner-мидлварь и вернуть ее же."""
        return self.inner.register(middleware)

    def unregister(self, middleware: BaseMiddleware[_UpdateT]) -> None:
        """Убрать inner-мидлварь."""
        self.inner.unregister(middleware)
