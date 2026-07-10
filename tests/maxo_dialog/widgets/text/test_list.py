from typing import Any, cast

import pytest

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.text import Const, Format, List


async def test_list_renders_all_items_without_pagination(
    mock_manager: DialogManager,
) -> None:
    widget = List(Format("{pos}:{item}"), items="items", sep=", ")

    rendered = await widget.render_text({"items": ["a", "b"]}, mock_manager)

    assert rendered == "1:a, 2:b"
    assert await widget.get_page_count({"items": ["a", "b"]}, mock_manager) == 1


async def test_list_renders_requested_page(mock_manager: DialogManager) -> None:
    mock_manager.current_context().widget_data["list"] = 1
    widget = List(
        Format("{current_page1}/{pages}:{pos0}:{item}"),
        items=lambda data: data["items"],
        id="list",
        page_size=2,
        sep="|",
    )

    rendered = await widget.render_text(
        {"items": ["a", "b", "c", "d", "e"]},
        mock_manager,
    )

    assert rendered == "2/3:2:c|2/3:3:d"
    assert await widget.get_page_count({"items": ["a", "b", "c"]}, mock_manager) == 2


async def test_list_clamps_page_to_last_available(
    mock_manager: DialogManager,
) -> None:
    mock_manager.current_context().widget_data["list"] = 10
    widget = List(
        Format("{current_page}:{item}"),
        items="items",
        id="list",
        page_size=2,
    )

    rendered = await widget.render_text({"items": ["a", "b", "c"]}, mock_manager)

    assert rendered == "1:c"


async def test_list_returns_empty_text_for_empty_items(
    mock_manager: DialogManager,
) -> None:
    widget = List(Const("never"), items=lambda _data: [], id="list", page_size=10)

    assert await widget.render_text({}, mock_manager) == ""
    assert await widget.get_page_count({}, mock_manager) == 0


def test_list_accepts_callable_items_getter() -> None:
    def items_getter(data: dict[Any, Any]) -> list[str]:
        return cast(list[str], data["items"])

    widget = List(Const("item"), items=items_getter)

    assert widget.items_getter({"items": ["a"]}) == ["a"]


def test_list_requires_id_when_paginated() -> None:
    # без id все постраничные List делили бы один ключ в widget_data
    with pytest.raises(ValueError, match="page_size"):
        List(Const("x"), items=lambda _data: [1, 2], page_size=2)


def test_list_without_id_and_page_size_has_no_widget_id() -> None:
    widget = List(Const("x"), items=lambda _data: [1, 2])

    assert widget.widget_id is None
