from unittest.mock import AsyncMock, Mock

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import Counter
from maxo.dialogs.widgets.text import Const
from maxo.routing.updates import MessageCallback
from maxo.types import Callback, User
from tests.constants import NOW


async def test_set_value_counter(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter")

    assert counter.get_value(mock_manager) == 0

    await counter.set_value(mock_manager, 1)

    assert counter.get_value(mock_manager) == 1


async def test_min_value_counter(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter", min_value=10)

    assert counter.get_value(mock_manager) == 0

    await counter.set_value(mock_manager, 1)

    assert counter.get_value(mock_manager) == 0


async def test_max_value_counter(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter", max_value=10)

    assert counter.get_value(mock_manager) == 0

    await counter.set_value(mock_manager, 11)

    assert counter.get_value(mock_manager) == 0


def test_default_counter(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter", default=10)

    assert counter.get_value(mock_manager) == 10


async def test_on_value_changed_counter(mock_manager: DialogManager) -> None:
    on_value_changed = AsyncMock()
    counter = Counter(id="counter", on_value_changed=on_value_changed)

    await counter.set_value(mock_manager, 1)

    on_value_changed.assert_called_once()


async def test_render_keyboard_counter(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter")
    keyboard = await counter._render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert len(keyboard[0]) == 3
    assert keyboard[0][0].text == "-"
    assert keyboard[0][1].text == "0"
    assert keyboard[0][2].text == "+"


async def test_render_keyboard_without_plus(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter", plus=None)
    keyboard = await counter._render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert len(keyboard[0]) == 2
    assert keyboard[0][0].text == "-"
    assert keyboard[0][1].text == "0"


async def test_render_keyboard_without_minus(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter", minus=None)
    keyboard = await counter._render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert len(keyboard[0]) == 2
    assert keyboard[0][0].text == "0"
    assert keyboard[0][1].text == "+"


async def test_render_keyboard_without_text(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter", text=None)
    keyboard = await counter._render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert len(keyboard[0]) == 2
    assert keyboard[0][0].text == "-"
    assert keyboard[0][1].text == "+"


async def test_render_keyboard_custom_text(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter", plus=Const("Plus"), minus=Const("Minus"))
    keyboard = await counter._render_keyboard({}, mock_manager)

    assert len(keyboard) == 1
    assert len(keyboard[0]) == 3
    assert keyboard[0][0].text == "Minus"
    assert keyboard[0][2].text == "Plus"


async def test_process_plus_callback(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter")
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
            payload="counter:+",
        ),
    )

    await counter._process_item_callback(callback, "+", Mock(), mock_manager)

    assert counter.get_value(mock_manager) == 1


async def test_process_minus_callback(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter", default=5)
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
            payload="counter:-",
        ),
    )

    await counter._process_item_callback(callback, "-", Mock(), mock_manager)

    assert counter.get_value(mock_manager) == 4


async def test_process_text_callback(mock_manager: DialogManager) -> None:
    on_text_click = AsyncMock()
    counter = Counter(id="counter", on_text_click=on_text_click)
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
            payload="counter:",
        ),
    )

    await counter._process_item_callback(callback, "", Mock(), mock_manager)

    on_text_click.assert_called_once()


async def test_cycle_max_overflow(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter", max_value=10, cycle=True)
    await counter.set_value(mock_manager, 10)
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
            payload="counter:+",
        ),
    )

    await counter._process_item_callback(callback, "+", Mock(), mock_manager)

    assert counter.get_value(mock_manager) == 0


async def test_cycle_min_underflow(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter", min_value=0, max_value=10, cycle=True)
    await counter.set_value(mock_manager, 0)
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
            payload="counter:-",
        ),
    )

    await counter._process_item_callback(callback, "-", Mock(), mock_manager)

    assert counter.get_value(mock_manager) == 10


async def test_on_click_callback(mock_manager: DialogManager) -> None:
    on_click = AsyncMock()
    counter = Counter(id="counter", on_click=on_click)
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
            payload="counter:+",
        ),
    )

    await counter._process_item_callback(callback, "+", Mock(), mock_manager)

    on_click.assert_called_once()


async def test_managed_counter(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter", default=5)
    managed = counter.managed(mock_manager)

    assert managed.get_value() == 5

    await managed.set_value(10)

    assert managed.get_value() == 10
