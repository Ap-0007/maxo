from collections.abc import Awaitable, Callable
from typing import Any, Final, Generic, TypeVar

from maxo.routing.ctx import Ctx
from maxo.routing.filters.base import BaseFilter
from maxo.routing.interfaces.filter import Filter
from maxo.routing.utils.callback_params import get_callback_params
from maxo.types.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)

# `self` передается методом, `update` и `ctx` - явно при вызове фильтра.
RESERVED_PARAMS: Final = frozenset({"self", "update", "ctx"})


class FilterObject(BaseFilter[_UpdateT], Generic[_UpdateT]):
    """
    Фильтр вместе с разобранной сигнатурой его `__call__`.

    Обернутый фильтр может попросить значения из контекста, объявив их
    параметрами `__call__`. Сигнатура разбирается один раз, при регистрации:
    фильтры зовутся на каждый апдейт, и `inspect` там был бы слишком дорогим.

    Сам является фильтром, поэтому его можно передавать всюду, где ждут `Filter`.
    """

    filter: Filter[_UpdateT]

    __slots__ = ("_params", "_varkw", "filter")

    def __init__(self, filter_: Filter[_UpdateT]) -> None:
        if isinstance(filter_, FilterObject):
            filter_ = filter_.filter

        self.filter = filter_

        try:
            params, self._varkw = get_callback_params(type(filter_).__call__)
        except TypeError:
            self._params: frozenset[str] = frozenset()
            self._varkw = False
        else:
            self._params = frozenset(params) - RESERVED_PARAMS

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.filter!r})"

    def _prepare_kwargs(self, ctx: Ctx) -> dict[str, Any]:
        if self._varkw:
            return {
                key: value for key, value in ctx.items() if key not in RESERVED_PARAMS
            }

        return {key: ctx[key] for key in self._params if key in ctx}

    async def call(self, update: _UpdateT, ctx: Ctx) -> bool:
        callback: Callable[..., Awaitable[bool]] = self.filter
        return await callback(update, ctx=ctx, **self._prepare_kwargs(ctx))

    __call__ = call


def unwrap_filter(filter_: Filter[_UpdateT]) -> Filter[_UpdateT]:
    if isinstance(filter_, FilterObject):
        return filter_.filter

    return filter_
