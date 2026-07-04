from typing import Any, cast

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
