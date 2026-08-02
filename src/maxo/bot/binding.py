import dataclasses
import sys
import typing
from functools import cache
from typing import TYPE_CHECKING, Any, Final, TypeAlias

from maxo.types.base import BaseMaxoType, BotMixin

if TYPE_CHECKING:
    from maxo.bot.bot import Bot


def _flatten(hint: Any) -> list[Any]:
    """Развернуть хинт: `list[Message] | None` -> он сам, `list[Message]`, `Message`."""
    found = [hint]
    for arg in typing.get_args(hint):
        found.extend(_flatten(arg))
    return found


@cache
def _field_models(tp: Any) -> tuple[tuple[str, tuple[type, ...]], ...]:
    """Для каждого поля - модели, которые могут в нем лежать."""
    if not dataclasses.is_dataclass(tp):
        return ()

    hints = typing.get_type_hints(tp, globalns=vars(sys.modules[tp.__module__]))
    return tuple(
        (
            field.name,
            tuple(
                hint
                for hint in _flatten(hints.get(field.name, field.type))
                if isinstance(hint, type) and issubclass(hint, BaseMaxoType)
            ),
        )
        for field in dataclasses.fields(tp)
    )


_BINDS: dict[type, bool] = {}


def _binds_bot(tp: Any) -> bool:
    """
    Найдется ли BotMixin в самом tp или в его полях на любой глубине.

    По ответу решается, спускаться ли в такое поле при обходе. DFS + memo,
    граф ациклический (test_type_graph_is_acyclic), поэтому рекурсия конечна.
    """
    binds = _BINDS.get(tp)
    if binds is None:
        binds = _BINDS[tp] = issubclass(tp, BotMixin) or any(
            _binds_bot(model) for _, models in _field_models(tp) for model in models
        )
    return binds


def warm(*roots: Any) -> None:
    """
    Посчитать планы заранее, чтобы первый bind_bot не платил за интроспекцию.

    DFS + seen: один тип встречается сразу во многих ветках.
    """
    stack = [
        hint
        for root in roots
        for hint in _flatten(root)
        if isinstance(hint, type) and issubclass(hint, BaseMaxoType)
    ]
    seen: set[type] = set()

    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)

        _, names = _PLANS[current]
        for name, models in _field_models(current):
            if name in names:
                stack.extend(models)

_SEQUENCE: Final = "<sequence>"
_MAPPING: Final = "<mapping>"

_Plan: TypeAlias = tuple[bool, tuple[str, ...] | str]
_SKIP: Final[_Plan] = (False, ())


class _Plans(dict[type, _Plan]):
    """План на класс: ставить ли бота и в какие поля спускаться."""

    def __missing__(self, class_: type) -> _Plan:
        plan: _Plan

        if issubclass(class_, (list, tuple)):
            plan = (False, _SEQUENCE)
        elif issubclass(class_, dict):  # UploadMediaResult.photos
            plan = (False, _MAPPING)
        elif issubclass(class_, BaseMaxoType):
            plan = (
                issubclass(class_, BotMixin),
                tuple(
                    name
                    for name, models in _field_models(class_)
                    if any(_binds_bot(model) for model in models)
                ),
            )
        elif issubclass(class_, BotMixin):
            # Фасады: бота ставим, но спускаться некуда - это не dataclass.
            plan = (True, ())
        else:
            plan = _SKIP

        self[class_] = plan
        return plan


_PLANS = _Plans()


def bind_bot[T](obj: T, bot: "Bot") -> T:
    """
    Проставить бота всем `BotMixin` внутри `obj`.

    DFS + stack, без seen: загрузчик строит дерево, общих узлов не бывает.
    """
    stack: list[Any] = [obj]

    while stack:
        current = stack.pop()
        set_bot, names = _PLANS[current.__class__]

        if names is _SEQUENCE:
            stack.extend(current)
            continue

        if names is _MAPPING:
            stack.extend(current.values())
            continue

        if set_bot:
            current._bot = bot  # noqa: SLF001

        for name in names:
            value = getattr(current, name)
            if value is not None:
                stack.append(value)

    return obj
