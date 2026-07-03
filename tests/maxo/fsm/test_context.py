from collections.abc import MutableMapping
from typing import Any

from maxo.fsm.context import FSMContext
from maxo.fsm.key_builder import StorageKey
from maxo.fsm.state import State
from maxo.fsm.storages.memory import MemoryStorage


def make_context(
    *,
    storage: MemoryStorage | None = None,
    chat_id: int = -42,
    user_id: int = 42,
    bot_id: int = 1,
) -> FSMContext:
    if storage is None:
        storage = MemoryStorage()
    return FSMContext(
        storage=storage,
        key=StorageKey(chat_id=chat_id, user_id=user_id, bot_id=bot_id),
    )


async def test_context_isolated_by_storage_key() -> None:
    storage = MemoryStorage()
    state = make_context(storage=storage)
    state2 = make_context(storage=storage, chat_id=42)
    state3 = make_context(storage=storage, chat_id=69, user_id=69)

    await state.set_state(State("test", group_name="Group"))
    await state.set_data({"foo": "bar"})

    assert await state.get_state() == "Group:test"
    assert await state2.get_state() is None
    assert await state3.get_state() is None
    assert await state.get_data() == {"foo": "bar"}
    assert await state2.get_data() == {}
    assert await state3.get_data() == {}
    assert await state.get_value("foo") == "bar"
    assert await state2.get_value("foo") is None
    assert await state3.get_value("foo", "baz") == "baz"

    await state2.set_state(State("experiments", group_name="Group"))
    await state3.set_data({"key": "value"})

    assert await state.get_state() == "Group:test"
    assert await state2.get_state() == "Group:experiments"
    assert await state3.get_data() == {"key": "value"}
    assert await state2.get_data() == {}

    assert await state.update_data({"key": "value"}) == {
        "foo": "bar",
        "key": "value",
    }
    assert await state.get_data() == {"foo": "bar", "key": "value"}

    await state.clear()

    assert await state.get_state() is None
    assert await state.get_data() == {}
    assert await state2.get_state() == "Group:experiments"


async def test_update_data_merges_mapping_and_kwargs() -> None:
    state = make_context()

    result = await state.update_data({"foo": "bar"}, baz="spam")

    assert result == {"foo": "bar", "baz": "spam"}
    assert await state.get_data() == {"foo": "bar", "baz": "spam"}


async def test_set_data_accepts_mutable_mapping() -> None:
    class CustomMapping(dict[str, Any]):
        pass

    state = make_context()
    data: MutableMapping[str, Any] = CustomMapping(foo="bar")

    await state.set_data(data)

    assert await state.get_data() == {"foo": "bar"}
