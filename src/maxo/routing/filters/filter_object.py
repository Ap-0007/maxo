import inspect
from typing import Any, Final, Generic, TypeVar

from maxo.routing.ctx import Ctx
from maxo.routing.filters.base import BaseFilter
from maxo.routing.interfaces.filter import Filter
from maxo.types.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)

# Эти имена фильтр получает позиционно, из контекста их брать не нужно.
RESERVED_PARAMS: Final = frozenset({"self", "update", "ctx"})


class FilterObject(BaseFilter[_UpdateT], Generic[_UpdateT]):
    """
    Фильтр вместе с разобранной сигнатурой его `__call__`.

    Сам является фильтром: вызывается как `(update, ctx)` и комбинируется
    операторами `&`, `|`, `~`, поэтому его можно передавать всюду, где ждут
    `Filter`.

    Кроме `update` и `ctx` обернутый фильтр может попросить любое значение из
    контекста - достаточно объявить его параметром `__call__` с тем же именем.
    Сигнатура разбирается один раз, при регистрации: фильтры зовутся на каждый
    апдейт, и `inspect` в этом месте был бы слишком дорогим.

    Подражание aiogram, где ту же роль играет `FilterObject`.
    """

    filter: Filter[_UpdateT]

    __slots__ = ("_params", "_varkw", "filter")

    def __init__(self, filter_: Filter[_UpdateT]) -> None:
        # Обертка идемпотентна: заворачивать обертку в обертку незачем
        if isinstance(filter_, FilterObject):
            filter_ = filter_.filter

        self.filter = filter_

        try:
            spec = inspect.getfullargspec(type(filter_).__call__)
        except TypeError:
            # `__call__` не питоновская функция (например, C-level callable).
            self._params: frozenset[str] = frozenset()
            self._varkw = False
        else:
            self._params = frozenset({*spec.args, *spec.kwonlyargs}) - RESERVED_PARAMS
            self._varkw = spec.varkw is not None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.filter!r})"

    def _prepare_kwargs(self, ctx: Ctx) -> dict[str, Any]:
        if self._varkw:
            return {
                key: value for key, value in ctx.items() if key not in RESERVED_PARAMS
            }

        return {key: ctx[key] for key in self._params if key in ctx}

    async def call(self, update: _UpdateT, ctx: Ctx) -> bool:
        return await self.filter(update, ctx, **self._prepare_kwargs(ctx))

    __call__ = call


def unwrap_filter(filter_: Filter[_UpdateT]) -> Filter[_UpdateT]:
    """Достает исходный фильтр из обертки, если он в нее завернут."""
    if isinstance(filter_, FilterObject):
        return filter_.filter

    return filter_
