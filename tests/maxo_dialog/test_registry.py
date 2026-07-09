import pytest

from maxo import Dispatcher
from maxo.dialogs import Dialog, Window
from maxo.dialogs.api.exceptions import UnregisteredDialogError
from maxo.dialogs.setup import DialogRegistry
from maxo.dialogs.widgets.text import Const
from maxo.fsm import State, StatesGroup


class SG(StatesGroup):
    main = State()


@pytest.fixture
def registry() -> DialogRegistry:
    dp = Dispatcher()
    dp.include(Dialog(Window(Const("hi"), state=SG.main)))
    return DialogRegistry(dp)


def test_find_dialog_by_state(registry: DialogRegistry) -> None:
    assert registry.find_dialog(SG.main).states_group() is SG


def test_find_dialog_by_states_group_name(registry: DialogRegistry) -> None:
    # раньше строка уходила в `state.group` и падала с AttributeError
    assert registry.find_dialog("SG").states_group() is SG


def test_find_dialog_unknown_name(registry: DialogRegistry) -> None:
    with pytest.raises(UnregisteredDialogError, match="NoSuchGroup"):
        registry.find_dialog("NoSuchGroup")


def test_find_dialog_unregistered_state(registry: DialogRegistry) -> None:
    class Other(StatesGroup):
        first = State()

    with pytest.raises(UnregisteredDialogError):
        registry.find_dialog(Other.first)
