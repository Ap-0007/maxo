from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.text import Const, ScrollingText


async def test_scrolling_text_renders_current_page(
    mock_manager: DialogManager,
) -> None:
    mock_manager.current_context().widget_data["scroll"] = 1
    widget = ScrollingText(Const("abcdef"), id="scroll", page_size=2)

    assert await widget.render_text({}, mock_manager) == "cd"


async def test_scrolling_text_clamps_to_last_page(
    mock_manager: DialogManager,
) -> None:
    mock_manager.current_context().widget_data["scroll"] = 10
    widget = ScrollingText(Const("abcde"), id="scroll", page_size=2)

    assert await widget.render_text({}, mock_manager) == "e"


async def test_scrolling_text_get_page_count(mock_manager: DialogManager) -> None:
    widget = ScrollingText(Const("abcde"), id="scroll", page_size=2)

    assert await widget.get_page_count({}, mock_manager) == 3
