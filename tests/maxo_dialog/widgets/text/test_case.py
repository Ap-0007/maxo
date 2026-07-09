from typing import cast
from unittest.mock import MagicMock

from magic_filter import F

from maxo.dialogs import DialogManager
from maxo.dialogs.api.internal import TextWidget
from maxo.dialogs.widgets.text import Case, Const, Format


class FindableConst(Const):
    def __init__(self, text: str, widget_id: str) -> None:
        super().__init__(text)
        self.widget_id = widget_id

    def find(self, widget_id: str) -> TextWidget | None:
        if widget_id == self.widget_id:
            return self
        return None


async def test_render_case(mock_manager: DialogManager) -> None:
    case = Case(
        {
            0: Format("{number} is even!"),
            1: Const("It is Odd"),
        },
        selector=F["number"] % 2,
    )

    rendered_text = await case.render_text(
        data={"number": 10},
        manager=mock_manager,
    )

    assert rendered_text == "10 is even!"


async def test_render_case_uses_default(mock_manager: DialogManager) -> None:
    case = Case(
        {
            "known": Const("known"),
            ...: Const("default"),
        },
        selector="value",
    )

    assert await case.render_text({"value": "missing"}, mock_manager) == "default"


async def test_render_case_uses_first_text_in_preview(
    mock_manager: DialogManager,
) -> None:
    is_preview = cast(MagicMock, mock_manager.is_preview)
    is_preview.return_value = True
    case = Case(
        {
            "first": Const("first"),
            "second": Const("second"),
        },
        selector=lambda _data, _case, _manager: "missing",
    )

    assert await case.render_text({}, mock_manager) == "first"


def test_case_find_nested_text() -> None:
    target = FindableConst("target", widget_id="target")
    case = Case(
        {
            "first": Const("first"),
            "second": target,
        },
        selector="value",
    )

    assert case.find("target") is target
    assert case.find("missing") is None
