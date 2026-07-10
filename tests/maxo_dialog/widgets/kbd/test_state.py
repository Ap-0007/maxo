from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities import ShowMode, StartMode
from maxo.dialogs.widgets.kbd import Back, Cancel, Next, Start, SwitchTo
from maxo.dialogs.widgets.kbd.state import EventProcessorButton
from maxo.dialogs.widgets.text import Const
from maxo.fsm import State, StatesGroup


class SG(StatesGroup):
    first = State()
    second = State()


@pytest.fixture
def manager() -> MagicMock:
    manager = MagicMock()
    manager.switch_to = AsyncMock()
    manager.next = AsyncMock()
    manager.back = AsyncMock()
    manager.done = AsyncMock()
    manager.start = AsyncMock()
    return manager


async def click(button: EventProcessorButton, manager: DialogManager) -> None:
    await button.process_event(MagicMock(), button, manager)


class TestSwitchTo:
    async def test_switches_state(self, manager: MagicMock) -> None:
        await click(SwitchTo(Const("b"), id="b", state=SG.second), manager)

        manager.switch_to.assert_awaited_once_with(SG.second, show_mode=None)

    async def test_calls_user_on_click(self, manager: MagicMock) -> None:
        on_click = AsyncMock()
        button = SwitchTo(Const("b"), id="b", state=SG.second, on_click=on_click)

        await click(button, manager)

        on_click.assert_awaited_once()


class TestNext:
    async def test_goes_next(self, manager: MagicMock) -> None:
        await click(Next(), manager)

        manager.next.assert_awaited_once_with(None)

    async def test_calls_user_on_click(self, manager: MagicMock) -> None:
        on_click = AsyncMock()

        await click(Next(on_click=on_click), manager)

        on_click.assert_awaited_once()


class TestBack:
    async def test_goes_back(self, manager: MagicMock) -> None:
        await click(Back(show_mode=ShowMode.EDIT), manager)

        manager.back.assert_awaited_once_with(ShowMode.EDIT)

    async def test_calls_user_on_click(self, manager: MagicMock) -> None:
        on_click = AsyncMock()

        await click(Back(on_click=on_click), manager)

        on_click.assert_awaited_once()


class TestCancel:
    async def test_finishes_dialog(self, manager: MagicMock) -> None:
        await click(Cancel(result={"r": 1}), manager)

        manager.done.assert_awaited_once_with({"r": 1}, show_mode=None)

    async def test_calls_user_on_click(self, manager: MagicMock) -> None:
        on_click = AsyncMock()

        await click(Cancel(on_click=on_click), manager)

        on_click.assert_awaited_once()


class TestStart:
    async def test_starts_dialog(self, manager: MagicMock) -> None:
        button = Start(
            Const("b"),
            id="b",
            state=SG.second,
            data={"d": 1},
            mode=StartMode.RESET_STACK,
        )

        await click(button, manager)

        kwargs: dict[str, Any] = manager.start.await_args.kwargs
        assert kwargs["state"] == SG.second
        assert kwargs["data"] == {"d": 1}
        assert kwargs["mode"] is StartMode.RESET_STACK

    async def test_calls_user_on_click(self, manager: MagicMock) -> None:
        on_click = AsyncMock()
        button = Start(Const("b"), id="b", state=SG.second, on_click=on_click)

        await click(button, manager)

        on_click.assert_awaited_once()


async def test_base_on_click_is_abstract(manager: MagicMock) -> None:
    button = EventProcessorButton(Const("b"), id="b")

    with pytest.raises(NotImplementedError):
        await click(button, manager)
