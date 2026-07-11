from typing import cast
from unittest.mock import AsyncMock, Mock

from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities import ChatEvent
from maxo.dialogs.widgets.kbd import Checkbox
from maxo.dialogs.widgets.text import Const
from maxo.types import Callback, CallbackButton, MessageCallback, User
from tests.constants import NOW


async def test_check_checkbox(mock_manager: DialogManager) -> None:
    checkbox = Checkbox(
        Const("✓  Checked"),
        Const("Unchecked"),
        id="check",
        default=True,
    )

    assert checkbox.is_checked(mock_manager)

    await checkbox.set_checked(cast(ChatEvent, Mock()), False, mock_manager)

    assert not checkbox.is_checked(mock_manager)


async def test_on_state_changed_checkbox(mock_manager: DialogManager) -> None:
    on_state_changed = AsyncMock()
    checkbox = Checkbox(
        Const("✓  Checked"),
        Const("Unchecked"),
        id="check",
        on_state_changed=on_state_changed,
    )

    await checkbox.set_checked(cast(ChatEvent, Mock()), False, mock_manager)

    on_state_changed.assert_called_once()


async def test_render_keyboard_checked(mock_manager: DialogManager) -> None:
    checkbox = Checkbox(
        Const("✓  Checked"),
        Const("Unchecked"),
        id="check",
        default=True,
    )

    keyboard = await checkbox._render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert len(keyboard[0]) == 1
    button = keyboard[0][0]
    assert isinstance(button, CallbackButton)
    assert button.text == "✓  Checked"
    assert "check:1" in button.payload


async def test_render_keyboard_unchecked(mock_manager: DialogManager) -> None:
    checkbox = Checkbox(
        Const("✓  Checked"),
        Const("Unchecked"),
        id="check",
        default=False,
    )

    keyboard = await checkbox._render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert len(keyboard[0]) == 1
    button = keyboard[0][0]
    assert isinstance(button, CallbackButton)
    assert button.text == "Unchecked"
    assert "check:0" in button.payload


async def test_process_item_callback_toggle(mock_manager: DialogManager) -> None:
    checkbox = Checkbox(
        Const("✓  Checked"),
        Const("Unchecked"),
        id="check",
        default=False,
    )

    fake_user = User(
        user_id=1,
        is_bot=False,
        first_name="Test",
        last_activity_time=NOW,
    )
    callback = MessageCallback(
        timestamp=NOW,
        callback=Callback(
            callback_id="1",
            user=fake_user,
            timestamp=NOW,
            payload="check:0",
        ),
    )

    assert not checkbox.is_checked(mock_manager)

    await checkbox._process_item_callback(callback, "0", Mock(), mock_manager)

    assert checkbox.is_checked(mock_manager)


async def test_on_click_callback(mock_manager: DialogManager) -> None:
    on_click = AsyncMock()
    checkbox = Checkbox(
        Const("✓  Checked"),
        Const("Unchecked"),
        id="check",
        on_click=on_click,
    )

    fake_user = User(
        user_id=1,
        is_bot=False,
        first_name="Test",
        last_activity_time=NOW,
    )
    callback = MessageCallback(
        timestamp=NOW,
        callback=Callback(
            callback_id="1",
            user=fake_user,
            timestamp=NOW,
            payload="check:0",
        ),
    )

    await checkbox._process_item_callback(callback, "0", Mock(), mock_manager)

    on_click.assert_called_once()


async def test_managed_checkbox(mock_manager: DialogManager) -> None:
    checkbox = Checkbox(
        Const("✓  Checked"),
        Const("Unchecked"),
        id="check",
        default=False,
    )

    managed = checkbox.managed(mock_manager)

    assert not managed.is_checked()

    await managed.set_checked(True)

    assert managed.is_checked()
