from typing import Any

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd.stub_scroll import StubScroll


class FakeDialogMagic:
    def __init__(self, value: Any) -> None:
        self._value = value

    def resolve(self, data: Any) -> Any:
        return self._value


async def test_stub_scroll_fixed_pages(mock_manager: DialogManager) -> None:
    scroll = StubScroll(id="scroll", pages=5)

    page_count = await scroll.get_page_count({}, mock_manager)

    assert page_count == 5


async def test_stub_scroll_field_pages(mock_manager: DialogManager) -> None:
    scroll = StubScroll(id="scroll", pages="total_pages")

    page_count = await scroll.get_page_count({"total_pages": 10}, mock_manager)

    assert page_count == 10


async def test_stub_scroll_render_keyboard(mock_manager: DialogManager) -> None:
    scroll = StubScroll(id="scroll", pages=3)

    keyboard = await scroll.render_keyboard({}, mock_manager)

    # StubScroll всегда возвращает пустую клавиатуру
    assert keyboard == [[]]


async def test_stub_scroll_field_pages_missing_key(
    mock_manager: DialogManager,
) -> None:
    scroll = StubScroll(id="scroll", pages="missing_key")

    page_count = await scroll.get_page_count({}, mock_manager)

    # Should return None when key is missing
    assert page_count is None


async def test_stub_scroll_with_int_zero(mock_manager: DialogManager) -> None:
    scroll = StubScroll(id="scroll", pages=0)

    page_count = await scroll.get_page_count({}, mock_manager)

    assert page_count == 0


async def test_stub_scroll_with_magic_filter(mock_manager: DialogManager) -> None:
    fake_magic = FakeDialogMagic(12)

    scroll = StubScroll(id="scroll", pages=fake_magic)

    page_count = await scroll.get_page_count({"items": [1, 2, 3]}, mock_manager)

    assert page_count == 12
