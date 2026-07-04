import operator
from unittest.mock import AsyncMock

from maxo.dialogs.widgets.kbd import Checkbox, Counter, Multiselect, Radio, Toggle
from maxo.dialogs.widgets.text import Const, Format


async def test_counter_value_changes() -> None:
    on_changed = AsyncMock()
    counter = Counter(id="counter", default=0, on_value_changed=on_changed)
    manager = mock_manager()

    assert counter.get_value(manager) == 0
    await counter.set_value(manager, 1)
    assert counter.get_value(manager) == 1
    on_changed.assert_called_once()


async def test_checkbox_state_changes() -> None:
    on_changed = AsyncMock()
    checkbox = Checkbox(
        Const("✓"),
        Const("x"),
        id="check",
        on_state_changed=on_changed,
        default=True,
    )
    manager = mock_manager()

    assert checkbox.is_checked(manager) is True
    await checkbox.set_checked(object(), False, manager)
    assert checkbox.is_checked(manager) is False
    on_changed.assert_called_once()


async def test_toggle_radio_multiselect_render_and_state() -> None:
    items = [("1", "Apple"), ("2", "Banana"), ("3", "Orange")]
    radio = Radio(
        Format("{item[1]}"),
        Format("x {item[1]}"),
        id="fruit",
        item_id_getter=operator.itemgetter(0),
        items=items,
    )
    multiselect = Multiselect(
        Format("✓ {item[1]}"),
        Format("{item[1]}"),
        id="multi",
        item_id_getter=operator.itemgetter(0),
        items=items,
    )
    toggle = Toggle(
        Format("{item[1]}"),
        id="toggle",
        item_id_getter=operator.itemgetter(0),
        items=items,
    )

    manager = mock_manager()
    radio_keyboard = await radio.render_keyboard({}, manager)
    multiselect_keyboard = await multiselect.render_keyboard({}, manager)
    toggle_keyboard = await toggle.render_keyboard({}, manager)

    assert radio_keyboard[0][0].text == "x Apple"
    assert multiselect_keyboard[0][0].text == "Apple"
    assert toggle_keyboard[0][0].text == "Apple"

    await radio.set_checked(object(), "2", manager)
    await multiselect.set_checked(object(), "1", True, manager)
    assert radio.get_checked(manager) == "2"
    assert multiselect.get_checked(manager) == ["1"]


async def test_multiselect_limits() -> None:
    multiselect = Multiselect(
        Format("✓ {item[1]}"),
        Format("{item[1]}"),
        id="multi",
        item_id_getter=operator.itemgetter(0),
        items=[("1", "Apple"), ("2", "Banana"), ("3", "Orange")],
        min_selected=2,
        max_selected=2,
    )

    manager = mock_manager()
    await multiselect.set_checked(object(), "1", True, manager)
    await multiselect.set_checked(object(), "2", True, manager)
    await multiselect.set_checked(object(), "3", True, manager)
    assert multiselect.get_checked(manager) == ["1", "2"]
    await multiselect.set_checked(object(), "2", False, manager)
    assert multiselect.get_checked(manager) == ["1", "2"]


def mock_manager() -> object:
    class Context:
        def __init__(self) -> None:
            self.widget_data: dict[str, object] = {}

    class Manager:
        def __init__(self) -> None:
            self.middleware_data: dict[str, object] = {}
            self.event = object()
            self._context = Context()

        def current_context(self) -> object:
            return self._context

        def is_preview(self) -> bool:
            return False

    return Manager()
