from datetime import UTC, datetime
from typing import cast
from unittest.mock import MagicMock, Mock

from maxo.dialogs import DialogManager
from maxo.dialogs.api.protocols import DialogProtocol
from maxo.dialogs.widgets.kbd import ListGroup
from maxo.dialogs.widgets.kbd.button import Button
from maxo.dialogs.widgets.kbd.pager import (
    CurrentPage,
    FirstPage,
    LastPage,
    NextPage,
    NumberedPager,
    PageDirection,
    PrevPage,
    SwitchPage,
)
from maxo.dialogs.widgets.text import Const, Format
from maxo.routing.updates import MessageCallback
from maxo.types import Callback, User


async def test_switch_page_first(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c", "d", "e"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = SwitchPage(PageDirection.FIRST, list_group, "pager", Const("First"))

    await list_group.set_page(Mock(), 2, mock_manager)
    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert keyboard[0][0].text == "First"


async def test_switch_page_last(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c", "d", "e"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = SwitchPage(PageDirection.LAST, list_group, "pager", Const("Last"))

    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert keyboard[0][0].text == "Last"


async def test_switch_page_next(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c", "d", "e"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = SwitchPage(PageDirection.NEXT, list_group, "pager", Const("Next"))

    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert keyboard[0][0].text == "Next"


async def test_switch_page_prev(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c", "d", "e"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = SwitchPage(PageDirection.PREV, list_group, "pager", Const("Prev"))

    await list_group.set_page(Mock(), 2, mock_manager)
    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert keyboard[0][0].text == "Prev"


async def test_switch_page_ignore(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c", "d", "e"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = SwitchPage(PageDirection.IGNORE, list_group, "pager", Const("Current"))

    await list_group.set_page(Mock(), 2, mock_manager)
    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert keyboard[0][0].text == "Current"


async def test_switch_page_int(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c", "d", "e"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = SwitchPage(2, list_group, "pager", Const("Page 3"))

    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert keyboard[0][0].text == "Page 3"


async def test_first_page(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = FirstPage(list_group)

    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert keyboard[0][0].text == "<<"


async def test_last_page(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = LastPage(list_group)

    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert keyboard[0][0].text == ">>"


async def test_next_page(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = NextPage(list_group)

    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert keyboard[0][0].text == ">"


async def test_prev_page(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = PrevPage(list_group)

    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert keyboard[0][0].text == "<"


async def test_current_page(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = CurrentPage(list_group)

    await list_group.set_page(Mock(), 1, mock_manager)
    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert keyboard[0][0].text == "2"


async def test_numbered_pager(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = NumberedPager(list_group)

    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert len(keyboard[0]) == 3
    assert keyboard[0][0].text == "[ 1 ]"
    assert keyboard[0][1].text == "2"
    assert keyboard[0][2].text == "3"


async def test_numbered_pager_with_length(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c", "d", "e"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = NumberedPager(list_group, length=3)

    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 2
    assert len(keyboard[0]) == 3
    assert len(keyboard[1]) == 2


async def test_process_item_callback(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = FirstPage(list_group)

    fake_user = User(
        user_id=1,
        is_bot=False,
        first_name="Test",
        last_activity_time=datetime(2026, 1, 1, tzinfo=UTC),
    )
    callback = MessageCallback(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        callback=Callback(
            callback_id="1",
            user=fake_user,
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            payload="pager:1",
        ),
    )

    await list_group.set_page(Mock(), 2, mock_manager)
    await pager._process_item_callback(
        callback,
        "1",
        cast(DialogProtocol, Mock()),
        mock_manager,
    )

    assert await list_group.get_page(mock_manager) == 1


async def test_find_scroll_by_id(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
        page_size=1,
    )

    cast(MagicMock, mock_manager.find).return_value = list_group.managed(mock_manager)

    pager = FirstPage("list")
    scroll = pager._find_scroll(mock_manager)

    assert scroll is not None
    cast(MagicMock, mock_manager.find).assert_called_once_with("list")


async def test_numbered_pager_custom_text(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
        page_size=1,
    )
    pager = NumberedPager(
        list_group,
        page_text=Format("Page {target_page1}"),
        current_page_text=Format(">> {current_page1} <<"),
    )

    keyboard = await pager.render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert len(keyboard[0]) == 3
    assert keyboard[0][0].text == ">> 1 <<"
    assert keyboard[0][1].text == "Page 2"
    assert keyboard[0][2].text == "Page 3"
