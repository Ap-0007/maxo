import dataclasses
import typing
from functools import cache
from typing import TYPE_CHECKING, Any, Final, NamedTuple

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
    """Для каждого поля - модели BaseMaxoType, спрятанные в хинте на любой глубине."""
    if not dataclasses.is_dataclass(tp):
        return ()

    hints = typing.get_type_hints(tp)
    field_models = []
    for field in dataclasses.fields(tp):
        hint = hints.get(field.name, field.type)

        models = []
        for part in _flatten(hint):
            if isinstance(part, type) and issubclass(part, BaseMaxoType):
                models.append(part)  # noqa: PERF401

        field_models.append((field.name, tuple(models)))

    return tuple(field_models)


@cache
def _binds_bot(tp: Any) -> bool:
    """
    Найдется ли BotMixin в самом tp или в его полях на любой глубине.

    По ответу решается, спускаться ли в такое поле при обходе. DFS + memo,
    граф ациклический (test_type_graph_is_acyclic), поэтому рекурсия конечна.
    """
    if issubclass(tp, BotMixin):
        return True

    for _, models in _field_models(tp):
        if any(_binds_bot(model) for model in models):
            return True

    return False


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

        _, _, fields = _PLANS[current]
        for name, models in _field_models(current):
            if name in fields:
                stack.extend(models)


_SEQUENCE: Final = object()
_MAPPING: Final = object()
_OBJECT: Final = object()


class Plan(NamedTuple):
    kind: object
    set_bot: bool = False
    fields: tuple[str, ...] = ()


_SKIP = Plan(kind=_OBJECT)


class _Plans(dict[type, Plan]):
    """Кэш `Plan` на класс, считается один раз при первом обращении."""

    def __missing__(self, class_: type) -> Plan:
        self[class_] = plan = self._compute_plan(class_)
        return plan

    @staticmethod
    def _compute_plan(class_: type) -> Plan:
        if issubclass(class_, (list, tuple)):
            return Plan(kind=_SEQUENCE)
        if issubclass(class_, dict):  # UploadMediaResult.photos
            return Plan(kind=_MAPPING)
        if issubclass(class_, BotMixin) and not issubclass(class_, BaseMaxoType):
            # Фасады: бота ставим, но спускаться некуда - это не dataclass.
            return Plan(kind=_OBJECT, set_bot=True)
        if not issubclass(class_, BaseMaxoType):
            return _SKIP

        bound_fields = []
        for name, models in _field_models(class_):
            field_binds_bot = any(_binds_bot(model) for model in models)
            if field_binds_bot:
                bound_fields.append(name)

        return Plan(
            kind=_OBJECT,
            set_bot=issubclass(class_, BotMixin),
            fields=tuple(bound_fields),
        )


_PLANS = _Plans()


def bind_bot[T](obj: T, bot: "Bot") -> T:
    """
    Проставить бота всем `BotMixin` внутри `obj`.

    DFS + stack, без seen: загрузчик строит дерево, общих узлов не бывает.
    """
    stack: list[Any] = [obj]

    while stack:
        current = stack.pop()
        kind, set_bot, fields = _PLANS[current.__class__]

        if kind is _SEQUENCE:
            stack.extend(current)
            continue

        if kind is _MAPPING:
            stack.extend(current.values())
            continue

        if set_bot:
            current._bot = bot  # noqa: SLF001

        for name in fields:
            value = getattr(current, name)
            if value is not None:
                stack.append(value)

    return obj
