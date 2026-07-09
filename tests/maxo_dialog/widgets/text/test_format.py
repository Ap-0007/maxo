from typing import cast
from unittest.mock import MagicMock

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.text import Format


async def test_render_format(mock_manager: DialogManager) -> None:
    format_widget = Format("Hello, {name}!")

    rendered_text = await format_widget.render_text(
        data={"name": "Tishka17"},
        manager=mock_manager,
    )

    assert rendered_text == "Hello, Tishka17!"


async def test_render_format_preview_keeps_missing_fields(
    mock_manager: DialogManager,
) -> None:
    is_preview = cast(MagicMock, mock_manager.is_preview)
    is_preview.return_value = True
    format_widget = Format("Hello, {user[name]:>10}! {known}")

    rendered_text = await format_widget.render_text(
        data={"known": "ready"},
        manager=mock_manager,
    )

    assert rendered_text == "Hello, {user[name]:>10}! ready"


async def test_render_format_preview_keeps_missing_attributes(
    mock_manager: DialogManager,
) -> None:
    is_preview = cast(MagicMock, mock_manager.is_preview)
    is_preview.return_value = True
    format_widget = Format("{event.from_user.id}")

    rendered_text = await format_widget.render_text({}, mock_manager)

    assert rendered_text == "{event.from_user.id}"
