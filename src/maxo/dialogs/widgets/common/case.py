from collections.abc import Callable, Hashable
from typing import Any, TypeVar, cast

from maxo.dialogs import DialogManager
from maxo.dialogs.integrations.magic_filter import DialogMagic

T = TypeVar("T")
Selector = Callable[[dict[Any, Any], T, DialogManager], Hashable]


def new_case_field(fieldname: str) -> Selector[T]:
    def case_field(
        data: dict[Any, Any],
        widget: T,
        manager: DialogManager,
    ) -> Hashable:
        return data.get(fieldname)

    return case_field


def new_magic_selector(f: DialogMagic) -> Selector[T]:
    def magic_selector(
        data: dict[Any, Any],
        widget: T,
        manager: DialogManager,
    ) -> Hashable:
        # Значение magic-фильтра - это ключ ветки `Case`, а не предикат,
        # поэтому его нельзя приводить к `bool`.
        return cast(Hashable, f.resolve(data))

    return magic_selector
