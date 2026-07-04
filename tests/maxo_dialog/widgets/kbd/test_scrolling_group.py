from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import ScrollingGroup
from maxo.dialogs.widgets.kbd.button import Button
from maxo.dialogs.widgets.text import Const
from maxo.routing.updates import MessageCallback
from maxo.types import Callback, User


async def test_scrolling_group_basic(mock_manager: DialogManager) -> None:
    scrolling = ScrollingGroup(
        Button(Const("Button 1"), "btn1"),
        Button(Const("Button 2"), "btn2"),
        Button(Const("Button 3"), "btn3"),
        id="scroll",
        height=2,
    )

    keyboard = await scrolling.render_keyboard({}, mock_manager)

    # Should have 2 buttons (height=2) + pager row
    assert len(keyboard) == 3
    assert keyboard[0][0].text == "Button 1"
    assert keyboard[1][0].text == "Button 2"
    # Pager row
    assert len(keyboard[2]) == 5


async def test_scrolling_group_pagination(mock_manager: DialogManager) -> None:
    scrolling = ScrollingGroup(
        Button(Const("Button 1"), "btn1"),
        Button(Const("Button 2"), "btn2"),
        Button(Const("Button 3"), "btn3"),
        Button(Const("Button 4"), "btn4"),
        id="scroll",
        height=2,
    )

    await scrolling.set_page(Mock(), 1, mock_manager)
    keyboard = await scrolling.render_keyboard({}, mock_manager)

    # Should show buttons 3 and 4 on page 1
    assert len(keyboard) == 3
    assert keyboard[0][0].text == "Button 3"
    assert keyboard[1][0].text == "Button 4"


async def test_scrolling_group_hide_pager(mock_manager: DialogManager) -> None:
    scrolling = ScrollingGroup(
        Button(Const("Button 1"), "btn1"),
        Button(Const("Button 2"), "btn2"),
        Button(Const("Button 3"), "btn3"),
        id="scroll",
        height=2,
        hide_pager=True,
    )

    keyboard = await scrolling.render_keyboard({}, mock_manager)

    # Should have only 2 buttons, no pager
    assert len(keyboard) == 2
    assert keyboard[0][0].text == "Button 1"
    assert keyboard[1][0].text == "Button 2"


async def test_scrolling_group_hide_on_single_page(mock_manager: DialogManager) -> None:
    scrolling = ScrollingGroup(
        Button(Const("Button 1"), "btn1"),
        Button(Const("Button 2"), "btn2"),
        id="scroll",
        height=2,
        hide_on_single_page=True,
    )

    keyboard = await scrolling.render_keyboard({}, mock_manager)

    # Should have only buttons, no pager because it's single page
    assert len(keyboard) == 2
    assert keyboard[0][0].text == "Button 1"
    assert keyboard[1][0].text == "Button 2"


async def test_scrolling_group_pager_buttons(mock_manager: DialogManager) -> None:
    scrolling = ScrollingGroup(
        Button(Const("Button 1"), "btn1"),
        Button(Const("Button 2"), "btn2"),
        Button(Const("Button 3"), "btn3"),
        Button(Const("Button 4"), "btn4"),
        id="scroll",
        height=2,
    )

    await scrolling.set_page(Mock(), 1, mock_manager)
    keyboard = await scrolling.render_keyboard({}, mock_manager)

    # Check pager buttons
    pager_row = keyboard[2]
    assert len(pager_row) == 5
    assert pager_row[0].text == "1"  # First page
    assert pager_row[1].text == "<"  # Previous
    assert pager_row[2].text == "2"  # Current page
    assert pager_row[3].text == ">"  # Next
    assert pager_row[4].text == "2"  # Last page


async def test_scrolling_group_process_item_callback(
    mock_manager: DialogManager,
) -> None:
    scrolling = ScrollingGroup(
        Button(Const("Button 1"), "btn1"),
        Button(Const("Button 2"), "btn2"),
        Button(Const("Button 3"), "btn3"),
        Button(Const("Button 4"), "btn4"),
        id="scroll",
        height=2,
    )

    fake_user = User(
        user_id=1,
        is_bot=False,
        first_name="Test",
        last_activity_time=datetime(2024, 1, 1, tzinfo=UTC),
    )
    callback = MessageCallback(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        callback=Callback(
            callback_id="1",
            user=fake_user,
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            payload="scroll:1",
        ),
    )

    result = await scrolling._process_item_callback(
        callback.callback,
        "1",
        None,
        mock_manager,
    )

    assert result is True
    assert await scrolling.get_page(mock_manager) == 1


async def test_scrolling_group_get_page_count(mock_manager: DialogManager) -> None:
    scrolling = ScrollingGroup(
        Button(Const("Button 1"), "btn1"),
        Button(Const("Button 2"), "btn2"),
        Button(Const("Button 3"), "btn3"),
        Button(Const("Button 4"), "btn4"),
        Button(Const("Button 5"), "btn5"),
        id="scroll",
        height=2,
    )

    page_count = await scrolling.get_page_count({}, mock_manager)

    assert page_count == 3  # 5 buttons / 2 height = 3 pages


async def test_scrolling_group_on_page_changed(mock_manager: DialogManager) -> None:
    on_page_changed = AsyncMock()
    scrolling = ScrollingGroup(
        Button(Const("Button 1"), "btn1"),
        Button(Const("Button 2"), "btn2"),
        Button(Const("Button 3"), "btn3"),
        id="scroll",
        height=1,
        on_page_changed=on_page_changed,
    )

    await scrolling.set_page(Mock(), 1, mock_manager)

    on_page_changed.assert_called_once()


async def test_scrolling_group_no_buttons(mock_manager: DialogManager) -> None:
    scrolling = ScrollingGroup(
        id="scroll",
        height=2,
    )

    keyboard = await scrolling.render_keyboard({}, mock_manager)

    # Empty group should return empty keyboard
    assert len(keyboard) == 0


async def test_scrolling_group_last_page_boundary(mock_manager: DialogManager) -> None:
    scrolling = ScrollingGroup(
        Button(Const("Button 1"), "btn1"),
        Button(Const("Button 2"), "btn2"),
        Button(Const("Button 3"), "btn3"),
        id="scroll",
        height=2,
    )

    # Try to set page beyond last page
    await scrolling.set_page(Mock(), 10, mock_manager)
    keyboard = await scrolling.render_keyboard({}, mock_manager)

    # Should clamp to last page (page 1, buttons 3)
    assert len(keyboard) == 2  # 1 button + pager
    assert keyboard[0][0].text == "Button 3"
