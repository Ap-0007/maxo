from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from magic_filter import F

from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities import ChatEvent
from maxo.dialogs.api.exceptions import InvalidWidgetIdError
from maxo.dialogs.widgets.common import (
    Actionable,
    BaseScroll,
    ManagedScroll,
    Selector,
    Whenable,
    new_case_field,
    new_magic_selector,
    sync_scroll,
)
from maxo.dialogs.widgets.common.items import get_items_getter
from maxo.dialogs.widgets.common.when import new_when_field, new_when_magic
from maxo.dialogs.widgets.data import (
    CompositeGetter,
    PreviewAwareGetter,
    StaticGetter,
)


class DummyScroll(BaseScroll):
    async def get_page_count(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> int:
        return 3


def test_actionable_validates_id() -> None:
    with pytest.raises(InvalidWidgetIdError, match="Invalid widget id"):
        Actionable(id="bad-id")


def test_actionable_find_and_repr(mock_manager: DialogManager) -> None:
    widget = Actionable(id="widget.id")

    assert widget.find("widget.id") is widget
    assert widget.find("missing") is None
    assert repr(widget) == "<Actionable id=widget.id>"
    assert widget.get_widget_data(mock_manager, "default") == "default"
    widget.set_widget_data(mock_manager, "value")
    assert widget.get_widget_data(mock_manager, "default") == "value"


def test_case_and_when_selectors(mock_manager: DialogManager) -> None:
    whenable = Whenable("enabled")
    case_selector: Selector[Whenable] = new_case_field("kind")

    assert case_selector({"kind": "A"}, whenable, mock_manager) == "A"
    assert new_when_field("enabled")({"enabled": 1}, whenable, mock_manager) is True
    assert whenable.is_({"enabled": True}, mock_manager) is True
    assert Whenable().is_({}, mock_manager) is True


def test_magic_selectors(mock_manager: DialogManager) -> None:
    whenable = Whenable(F["enabled"])
    magic_selector: Selector[Whenable] = new_magic_selector(F["enabled"])

    assert magic_selector({"enabled": True}, whenable, mock_manager) is True
    assert new_when_magic(F["enabled"])({"enabled": True}, whenable, mock_manager)
    assert whenable.is_({"enabled": True}, mock_manager) is True


def test_items_getters() -> None:
    assert get_items_getter("items")({"items": [1, 2]}) == [1, 2]
    assert get_items_getter([1, 2])({}) == [1, 2]
    assert get_items_getter(lambda data: data["items"])({"items": [3]}) == [3]
    assert get_items_getter(F["items"])({"items": [4]}) == [4]
    assert get_items_getter(F["items"])({"items": 1}) == []


async def test_base_scroll_and_managed_scroll(mock_manager: DialogManager) -> None:
    calls: list[int] = []

    async def on_page_changed(
        event: ChatEvent,
        widget: ManagedScroll,
        manager: DialogManager,
    ) -> None:
        calls.append(await widget.get_page())

    scroll = DummyScroll(id="scroll", on_page_changed=on_page_changed)
    managed = scroll.managed(mock_manager)

    assert await managed.get_page_count({}) == 3
    assert await managed.get_page() == 0
    await managed.set_page(2)
    assert await managed.get_page() == 2
    assert calls == [2]


async def test_sync_scroll_updates_other_scrolls(mock_manager: DialogManager) -> None:
    source = DummyScroll(id="source")
    target = DummyScroll(id="target")
    mock_manager.current_context().widget_data["source"] = 2
    manager_find = cast(MagicMock, mock_manager.find)
    manager_find.side_effect = lambda _widget_id: target.managed(mock_manager)

    await sync_scroll("target")(
        cast(ChatEvent, object()),
        source.managed(mock_manager),
        mock_manager,
    )

    assert await target.get_page(mock_manager) == 2


async def test_data_getters(mock_manager: DialogManager) -> None:
    async def first(**kwargs: Any) -> dict[str, int]:
        return {"first": kwargs["value"]}

    async def second(**kwargs: Any) -> dict[str, int]:
        return {"second": kwargs["value"] + 1}

    composite = CompositeGetter(first, second)
    static = StaticGetter({"static": 1})
    preview = PreviewAwareGetter(normal_getter=first, preview_getter=second)

    assert await composite(value=1) == {"first": 1, "second": 2}
    assert await static() == {"static": 1}
    assert await preview(dialog_manager=mock_manager, value=1) == {"first": 1}

    is_preview = cast(MagicMock, mock_manager.is_preview)
    is_preview.return_value = True
    assert await preview(dialog_manager=mock_manager, value=1) == {"second": 2}
