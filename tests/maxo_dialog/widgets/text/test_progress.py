from typing import cast
from unittest.mock import MagicMock

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.text import Progress


async def test_progress_renders_percent_from_data(mock_manager: DialogManager) -> None:
    widget = Progress("percent", width=5, filled="#", empty="-")

    rendered = await widget.render_text({"percent": 40}, mock_manager)

    assert rendered == "##---  40%"


async def test_progress_uses_default_zero(mock_manager: DialogManager) -> None:
    widget = Progress("percent", width=3, filled="#", empty="-")

    rendered = await widget.render_text({}, mock_manager)

    assert rendered == "---  0%"


async def test_progress_uses_preview_value(mock_manager: DialogManager) -> None:
    is_preview = cast(MagicMock, mock_manager.is_preview)
    is_preview.return_value = True
    widget = Progress("percent", width=10, filled="#", empty="-")

    rendered = await widget.render_text({"percent": 90}, mock_manager)

    assert rendered == "##--------  15%"
