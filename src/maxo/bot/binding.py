import dataclasses
import sys
import typing
from functools import cache
from typing import TYPE_CHECKING, Any

from maxo.types.base import BaseMaxoType, BotMixin

if TYPE_CHECKING:
    from maxo.bot.bot import Bot


def _flatten(hint: Any) -> list[Any]:
    """`Omittable[list[Message] | None]` и все типы, упомянутые внутри."""
    found = [hint]
    for arg in typing.get_args(hint):
        found.extend(_flatten(arg))
    return found


@cache
def _plan(tp: type) -> tuple[str, ...]:
    """Поля, в которые есть смысл спускаться - там, где может быть `BaseMaxoType`."""
    hints = typing.get_type_hints(tp, globalns=vars(sys.modules[tp.__module__]))
    return tuple(
        field.name
        for field in dataclasses.fields(tp)
        if any(
            isinstance(hint, type) and issubclass(hint, BaseMaxoType)
            for hint in _flatten(hints.get(field.name, field.type))
        )
    )


def warm(*roots: Any) -> None:
    seen: set[type] = set()

    def visit(hint: Any) -> None:
        for candidate in _flatten(hint):
            if not (
                isinstance(candidate, type) and issubclass(candidate, BaseMaxoType)
            ):
                continue
            if candidate in seen:
                continue
            seen.add(candidate)
            hints = typing.get_type_hints(
                candidate,
                globalns=vars(sys.modules[candidate.__module__]),
            )
            for name in _plan(candidate):
                visit(hints.get(name))

    for root in roots:
        visit(root)


def bind_bot[T](obj: T, bot: "Bot") -> T:
    if isinstance(obj, (list, tuple)):
        for item in obj:
            bind_bot(item, bot)
        return obj

    if isinstance(obj, dict):  # UploadMediaResult.photos
        for item in obj.values():
            bind_bot(item, bot)
        return obj

    if isinstance(obj, BotMixin):
        obj._bot = bot  # noqa: SLF001

    if not isinstance(obj, BaseMaxoType):
        return obj

    for name in _plan(type(obj)):
        bind_bot(getattr(obj, name), bot)
    return obj
