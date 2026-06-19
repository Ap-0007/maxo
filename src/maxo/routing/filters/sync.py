from collections.abc import Callable
from typing import TypeVar

from maxo.routing.ctx import Ctx
from maxo.routing.filters.base import BaseFilter
from maxo.routing.updates.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)


class SyncFilter(BaseFilter[_UpdateT]):
    """
    Обёртка для использования синхронной функции как фильтра.

    Принимает синк-функцию, которая по апдейту возвращает bool, и зовёт её
    напрямую. `to_thread` не используется: фильтры - hot-path предикаты на
    каждый апдейт, а лямбды тривиальны. Если функция блокирующая - оберните
    её в поток самостоятельно.
    """

    __slots__ = ("_func",)

    def __init__(self, func: Callable[[_UpdateT], bool]) -> None:
        self._func = func

    async def __call__(self, update: _UpdateT, ctx: Ctx) -> bool:
        return self._func(update)
