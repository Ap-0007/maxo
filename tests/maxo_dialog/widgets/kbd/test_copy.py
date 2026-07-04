from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import CopyText
from maxo.dialogs.widgets.text import Const, Format
from maxo.types import ClipboardButton


async def test_copy_text_basic(mock_manager: DialogManager) -> None:
    copy_text_widget = CopyText(
        text=Const("Copy this"),
        copy_text=Const("Text to be copied"),
    )

    keyboard = await copy_text_widget.render_keyboard(data={}, manager=mock_manager)

    button = keyboard[0][0]
    assert isinstance(button, ClipboardButton)
    assert button.text == "Copy this"
    assert button.payload == "Text to be copied"


async def test_copy_text_with_data(mock_manager: DialogManager) -> None:
    copy_text_widget = CopyText(
        text=Format("{label}"),
        copy_text=Format("{content}"),
    )

    keyboard = await copy_text_widget.render_keyboard(
        data={"label": "Copy Button", "content": "Dynamic content to copy"},
        manager=mock_manager,
    )

    button = keyboard[0][0]
    assert isinstance(button, ClipboardButton)
    assert button.text == "Copy Button"
    assert button.payload == "Dynamic content to copy"
