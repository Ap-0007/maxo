import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import TimeSelect


async def test_render_time_select(mock_manager: DialogManager) -> None:
    select = TimeSelect("x")

    keyboard_before = await select.render_keyboard(
        data={},
        manager=mock_manager,
    )

    assert len(keyboard_before) == 8

    await select.set_value(
        mock_manager.event,
        mock_manager,
        datetime.time(0, 10),
    )

    keyboard_after = await select.render_keyboard(
        data={},
        manager=mock_manager,
    )

    assert len(keyboard_after) == 8
    assert keyboard_after != keyboard_before


class TestValidation:
    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"minute_precision": 0}, "minute_precision"),
            ({"hour_width": 0}, "hour_width"),
            ({"minute_width": 0}, "minute_width"),
        ],
    )
    def test_rejects_non_positive_sizes(
        self,
        kwargs: dict[str, int],
        message: str,
    ) -> None:
        with pytest.raises(ValueError, match=message):
            TimeSelect("x", **kwargs)  # type: ignore[arg-type]


class TestValue:
    def test_value_is_none_by_default(self, mock_manager: DialogManager) -> None:
        assert TimeSelect("x").get_value(mock_manager) is None

    async def test_set_and_get_value(self, mock_manager: DialogManager) -> None:
        select = TimeSelect("x")

        await select.set_value(mock_manager.event, mock_manager, datetime.time(3, 15))

        assert select.get_value(mock_manager) == datetime.time(3, 15)

    async def test_reset_value(self, mock_manager: DialogManager) -> None:
        select = TimeSelect("x")
        await select.set_value(mock_manager.event, mock_manager, datetime.time(3, 15))

        await select.set_value(mock_manager.event, mock_manager, None)

        assert select.get_value(mock_manager) is None

    async def test_on_value_changed_is_called(
        self,
        mock_manager: DialogManager,
    ) -> None:
        on_value_changed = AsyncMock()
        select = TimeSelect("x", on_value_changed=on_value_changed)

        await select.set_value(mock_manager.event, mock_manager, datetime.time(1, 0))

        on_value_changed.assert_awaited_once()


class TestCallbacks:
    async def process(
        self,
        select: TimeSelect,
        data: str,
        manager: DialogManager,
    ) -> None:
        await select._process_item_callback(
            MagicMock(),
            data,
            MagicMock(),
            manager,
        )

    async def test_hour_click(self, mock_manager: DialogManager) -> None:
        on_hour_click = AsyncMock()
        select = TimeSelect("x", on_hour_click=on_hour_click)

        await self.process(select, "h7", mock_manager)

        on_hour_click.assert_awaited_once()
        assert select.get_widget_data(mock_manager, (None, None))[0] == 7

    async def test_minute_click(self, mock_manager: DialogManager) -> None:
        on_minute_click = AsyncMock()
        select = TimeSelect("x", on_minute_click=on_minute_click)

        await self.process(select, "m25", mock_manager)

        on_minute_click.assert_awaited_once()
        assert select.get_widget_data(mock_manager, (None, None))[1] == 25

    async def test_full_value_after_both_clicks(
        self,
        mock_manager: DialogManager,
    ) -> None:
        select = TimeSelect("x")

        await self.process(select, "h7", mock_manager)
        await self.process(select, "m25", mock_manager)

        assert select.get_value(mock_manager) == datetime.time(7, 25)

    async def test_unknown_callback_format(self, mock_manager: DialogManager) -> None:
        select = TimeSelect("x")

        with pytest.raises(ValueError, match="Unknown callback format"):
            await self.process(select, "zzz", mock_manager)


class TestManaged:
    async def test_managed_get_and_set(self, mock_manager: DialogManager) -> None:
        select = TimeSelect("x")
        managed = select.managed(mock_manager)

        assert managed.get_value() is None

        await managed.set_value(datetime.time(12, 30))

        assert managed.get_value() == datetime.time(12, 30)


async def test_render_marks_selected_values(mock_manager: DialogManager) -> None:
    select = TimeSelect("x", minute_precision=30)
    await select.set_value(mock_manager.event, mock_manager, datetime.time(1, 30))

    keyboard = await select.render_keyboard({}, mock_manager)
    texts = [b.text for row in keyboard for b in row]

    assert "[1]" in texts
    assert "[30]" in texts
