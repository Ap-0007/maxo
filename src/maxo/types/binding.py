import dataclasses
import typing
from functools import cache
from typing import TYPE_CHECKING, Any, Optional, Self

from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_defined

if TYPE_CHECKING:
    from maxo.bot.bot import Bot


class BotMixin:
    def __init__(self, bot: Optional["Bot"] = None) -> None:
        self._bot = bot

    def __post_init__(self) -> None:
        self._bot = None

    @property
    def bot(self) -> "Bot":
        if is_defined(self._bot):
            return self._bot

        raise AttributeIsEmptyError(
            obj=self,
            attr="_bot",
        )

    @bot.setter
    def bot(self, bot: Optional["Bot"]) -> None:
        bind_bot(self, bot)

    def as_(self, bot: Optional["Bot"]) -> Self:
        bind_bot(self, bot)
        return self


def _flatten(hint: Any) -> list[Any]:
    """Развернуть хинт: `list[Message] | None` -> он сам, `list[Message]`, `Message`."""
    if isinstance(hint, type):
        return [hint]

    found = []
    for arg in typing.get_args(hint):
        found.extend(_flatten(arg))

    return found


@cache
def _field_classes(class_: Any) -> dict[str, tuple[Any, ...]]:
    """Для каждого поля - модели BaseMaxoType, спрятанные в хинте на любой глубине."""
    if not dataclasses.is_dataclass(class_):
        return {}

    fields = dataclasses.fields(class_)
    hints = (
        typing.get_type_hints(class_)
        if any(isinstance(field.type, str) for field in fields)
        else {}
    )

    return {
        field.name: tuple(_flatten(hints.get(field.name, field.type)))
        for field in fields
    }


@cache
def _bot_fields(class_: Any) -> tuple[str, ...]:
    """
    Поля класса, внутри которых на любой глубине есть `BotMixin`.

    По ним `bind_bot` решает, спускаться ли в поле. Поле ведёт к боту, если его
    класс держит бота сам или содержит такое же поле глубже. Рекурсия конечна -
    граф типов ацикличен (`test_type_graph_is_acyclic`).
    """
    fields = []
    for name, classes in _field_classes(class_).items():
        leads_to_bot = any(
            issubclass(field_class, BotMixin) or _bot_fields(field_class)
            for field_class in classes
        )
        if leads_to_bot:
            fields.append(name)

    return tuple(fields)


def bind_bot[T](obj: T, bot: Optional["Bot"]) -> T:
    """
    Проставить бота всем `BotMixin` в дереве от `obj` вниз.

    DFS + стек, без `seen`: загрузчик строит дерево, общих узлов не бывает.
    """
    stack: list[Any] = [obj]

    while stack:
        node = stack.pop()

        if isinstance(node, (list, tuple)):
            stack.extend(node)
            continue
        if isinstance(node, dict):  # UploadMediaResult.photos
            stack.extend(node.values())
            continue
        if isinstance(node, BotMixin):
            node._bot = bot  # noqa: SLF001

        for name in _bot_fields(node.__class__):
            child = getattr(node, name)
            if child is not None:
                stack.append(child)

    return obj
