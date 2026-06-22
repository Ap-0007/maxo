import asyncio
from collections.abc import Callable
from typing import TypeVar

from maxo.routing.ctx import Ctx
from maxo.routing.filters.base import BaseFilter
from maxo.routing.updates.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)


class SyncFilter(BaseFilter[_UpdateT]):
    """
    Обёртка для использования синхронной функции как фильтра.

    Принимает синк-функцию, которая по апдейту возвращает bool. По умолчанию
    зовёт её напрямую: фильтры - hot-path предикаты на каждый апдейт, а лямбды
    тривиальны. Для блокирующих функций есть флаг `run_in_thread`, для
    подавления ошибок предиката - `exceptions_as_false`.
    """

    __slots__ = ("_exceptions_as_false", "_func", "_run_in_thread")

    def __init__(
        self,
        func: Callable[[_UpdateT], bool],
        *,
        run_in_thread: bool = False,
        exceptions_as_false: bool = False,
    ) -> None:
        """
        Создать фильтр-обёртку над синхронным предикатом.

        Args:
            func: синхронный предикат по апдейту.
            run_in_thread: выполнять `func` в отдельном потоке через
                `asyncio.to_thread` (для блокирующих функций).
            exceptions_as_false: ловить любую ошибку `func` и возвращать `False`
                вместо проброса исключения.

        """
        self._func = func
        self._run_in_thread = run_in_thread
        self._exceptions_as_false = exceptions_as_false

    async def __call__(self, update: _UpdateT, ctx: Ctx) -> bool:
        """Вызвать предикат и вернуть его bool-результат."""
        try:
            if self._run_in_thread:
                return await asyncio.to_thread(self._func, update)
            return self._func(update)
        except Exception:
            if self._exceptions_as_false:
                return False
            raise
