from typing import Any

from magic_filter import F

from maxo.dialogs.widgets.filter_object import CallableObject, FilterObject
from maxo.routing.ctx import Ctx
from maxo.routing.interfaces import Filter
from maxo.types import BaseUpdate


class DummyFilter(Filter[BaseUpdate]):
    async def __call__(self, update: BaseUpdate, ctx: Ctx) -> bool:
        return True

    def __and__(self, other: Filter[BaseUpdate] | Any) -> Filter[BaseUpdate]:
        return self

    def __or__(self, other: Filter[BaseUpdate] | Any) -> Filter[BaseUpdate]:
        return self

    def __invert__(self) -> Filter[BaseUpdate]:
        return self


async def test_callable_object_filters_kwargs_and_drops_update() -> None:
    def callback(value: int) -> int:
        return value + 1

    obj = CallableObject(callback)

    assert obj.awaitable is False
    assert obj.params == {"value"}
    assert obj.varkw is False
    assert await obj.call(value=1, extra=2, update=object()) == 2


async def test_callable_object_keeps_varkw() -> None:
    def callback(**kwargs: int) -> dict[str, int]:
        return kwargs

    obj = CallableObject(callback)

    assert obj.varkw is True
    assert await obj.call(value=1, extra=2) == {"value": 1, "extra": 2}


async def test_callable_object_awaits_async_callback() -> None:
    async def callback(value: int) -> int:
        return value + 1

    obj = CallableObject(callback)

    assert obj.awaitable is True
    assert await obj.call(value=1) == 2


async def test_filter_object_wraps_magic_filter() -> None:
    obj = FilterObject(F["enabled"])

    assert obj.magic is not None
    assert await obj.call({"enabled": True}) is True


async def test_filter_object_marks_routing_filter_awaitable() -> None:
    obj = FilterObject(DummyFilter())

    assert obj.awaitable is True
    assert await obj.call(object(), update=object(), ctx=Ctx({})) is True
