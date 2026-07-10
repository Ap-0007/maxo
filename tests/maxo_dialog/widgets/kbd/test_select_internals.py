import operator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, Mock

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import Multiselect, Radio, Select, Toggle
from maxo.dialogs.widgets.text import Format
from maxo.types import CallbackButton

ITEMS = [("1", "Apple"), ("2", "Banana"), ("3", "Orange")]


def make_select(**kwargs: Any) -> Select[Any]:
    return Select(
        Format("{item[1]}"),
        id="sel",
        item_id_getter=operator.itemgetter(0),
        items=ITEMS,
        **kwargs,
    )


def make_radio(**kwargs: Any) -> Radio[Any]:
    return Radio(
        Format("🔘 {item[1]}"),
        Format("⚪️ {item[1]}"),
        id="fruit",
        item_id_getter=operator.itemgetter(0),
        items=ITEMS,
        **kwargs,
    )


def make_multiselect(**kwargs: Any) -> Multiselect[Any]:
    return Multiselect(
        Format("✓ {item[1]}"),
        Format("{item[1]}"),
        id="fruits",
        item_id_getter=operator.itemgetter(0),
        items=ITEMS,
        **kwargs,
    )


def make_toggle(**kwargs: Any) -> Toggle[Any]:
    return Toggle(
        Format("{item[1]}"),
        id="tog",
        item_id_getter=operator.itemgetter(0),
        items=ITEMS,
        **kwargs,
    )


class TestSelect:
    async def test_item_callback_calls_on_click(
        self,
        mock_manager: DialogManager,
    ) -> None:
        on_click = AsyncMock()
        select = make_select(on_click=on_click)

        result = await select._process_item_callback(
            MagicMock(),
            "2",
            MagicMock(),
            mock_manager,
        )

        assert result is True
        on_click.assert_awaited_once()

    async def test_render_uses_item_id_in_payload(
        self,
        mock_manager: DialogManager,
    ) -> None:
        keyboard = await make_select().render_keyboard({}, mock_manager)
        payloads = [b.payload for b in keyboard[0] if isinstance(b, CallbackButton)]

        assert payloads == ["sel:1", "sel:2", "sel:3"]


class TestStatefulSelect:
    async def test_on_item_click_runs_before_state_change(
        self,
        mock_manager: DialogManager,
    ) -> None:
        on_item_click = AsyncMock()
        radio = make_radio(on_click=on_item_click)

        await radio._process_item_callback(
            MagicMock(),
            "2",
            MagicMock(),
            mock_manager,
        )

        on_item_click.assert_awaited_once()
        assert radio.get_checked(mock_manager) == "2"

    async def test_without_on_item_click(self, mock_manager: DialogManager) -> None:
        radio = make_radio()

        await radio._process_item_callback(
            MagicMock(),
            "2",
            MagicMock(),
            mock_manager,
        )

        assert radio.get_checked(mock_manager) == "2"


class TestRadioPreview:
    def test_is_text_checked_in_preview(self, mock_manager: DialogManager) -> None:
        cast(MagicMock, mock_manager).is_preview = Mock(return_value=True)
        radio = make_radio()

        # без сохранённого значения _preview_checked_id вернёт сам item_id
        assert radio._is_text_checked({"item": ITEMS[0]}, MagicMock(), mock_manager)

    def test_is_text_checked_outside_preview(
        self,
        mock_manager: DialogManager,
    ) -> None:
        radio = make_radio()

        assert not radio._is_text_checked({"item": ITEMS[0]}, MagicMock(), mock_manager)


class TestManagedRadio:
    async def test_managed_api(self, mock_manager: DialogManager) -> None:
        managed = make_radio().managed(mock_manager)

        assert managed.get_checked() is None

        await managed.set_checked("2")

        assert managed.get_checked() == "2"
        assert managed.is_checked("2") is True
        assert managed.is_checked("1") is False


class TestMultiselectPreview:
    def test_is_text_checked_in_preview_alternates(
        self,
        mock_manager: DialogManager,
    ) -> None:
        cast(MagicMock, mock_manager).is_preview = Mock(return_value=True)
        multiselect = make_multiselect()

        first = multiselect._is_text_checked(
            {"item": ITEMS[0]},
            MagicMock(),
            mock_manager,
        )
        second = multiselect._is_text_checked(
            {"item": ITEMS[1]},
            MagicMock(),
            mock_manager,
        )

        assert first != second


class TestMultiselectClicks:
    async def test_click_toggles_on_and_off(
        self,
        mock_manager: DialogManager,
    ) -> None:
        multiselect = make_multiselect()

        await multiselect._process_item_callback(
            MagicMock(),
            "2",
            MagicMock(),
            mock_manager,
        )
        assert multiselect.is_checked("2", mock_manager)

        await multiselect._process_item_callback(
            MagicMock(),
            "2",
            MagicMock(),
            mock_manager,
        )
        assert not multiselect.is_checked("2", mock_manager)


class TestManagedMultiselect:
    async def test_managed_api(self, mock_manager: DialogManager) -> None:
        managed = make_multiselect().managed(mock_manager)

        await managed.set_checked("1", checked=True)

        assert managed.is_checked("1") is True
        assert managed.get_checked() == ["1"]

        await managed.reset_checked()

        assert managed.get_checked() == []


class TestToggle:
    async def test_render_shows_only_current_item(
        self,
        mock_manager: DialogManager,
    ) -> None:
        toggle = make_toggle()

        keyboard = await toggle.render_keyboard({}, mock_manager)

        assert len(keyboard[0]) == 1
        assert keyboard[0][0].text == "Apple"

    async def test_render_advances_after_click(
        self,
        mock_manager: DialogManager,
    ) -> None:
        toggle = make_toggle()
        await toggle.set_checked(mock_manager.event, "1", mock_manager)

        keyboard = await toggle.render_keyboard({}, mock_manager)

        assert keyboard[0][0].text == "Apple"

    async def test_render_without_items(self, mock_manager: DialogManager) -> None:
        toggle: Toggle[Any] = Toggle(
            Format("{item}"),
            id="tog",
            item_id_getter=str,
            items=[],
        )

        assert await toggle.render_keyboard({}, mock_manager) == [[]]

    async def test_render_shows_selected_item(
        self,
        mock_manager: DialogManager,
    ) -> None:
        toggle = make_toggle()
        await toggle.set_checked(mock_manager.event, "3", mock_manager)

        keyboard = await toggle.render_keyboard({}, mock_manager)

        assert keyboard[0][0].text == "Orange"

    def test_managed_toggle(self, mock_manager: DialogManager) -> None:
        assert make_toggle().managed(mock_manager) is not None
