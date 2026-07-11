import asyncio
from typing import Any

from maxo.fsm.state import State
from maxo.fsm.storages.memory import (
    DisabledEventIsolation,
    MemoryStorage,
    SimpleEventIsolation,
)

from .conftest import make_key


async def test_memory_storage_state_isolated_by_key() -> None:
    storage = MemoryStorage()
    key = make_key()
    other_key = make_key(chat_id=69, user_id=69)

    assert await storage.get_state(key) is None

    await storage.set_state(key, State("state", group_name="Group"))

    assert await storage.get_state(key) == "Group:state"
    assert await storage.get_state(other_key) is None

    await storage.set_state(key)

    assert await storage.get_state(key) is None


async def test_memory_storage_data_isolated_and_copied() -> None:
    storage = MemoryStorage()
    key = make_key()
    data: dict[str, Any] = {"foo": "bar", "items": [1, 2]}

    assert await storage.get_data(key) == {}
    assert await storage.get_value(storage_key=key, value_key="foo") is None
    assert await storage.get_value(storage_key=key, value_key="foo", default="baz") == (
        "baz"
    )

    await storage.set_data(key, data)
    data["foo"] = "changed"

    stored = await storage.get_data(key)
    stored["foo"] = "mutated"

    assert await storage.get_data(key) == {"foo": "bar", "items": [1, 2]}
    assert await storage.get_value(storage_key=key, value_key="foo") == "bar"

    items = await storage.get_value(storage_key=key, value_key="items")
    assert items == [1, 2]
    assert items is not data["items"]


async def test_memory_storage_update_data() -> None:
    storage = MemoryStorage()
    key = make_key()

    assert await storage.update_data(key, {"foo": "bar"}) == {"foo": "bar"}
    assert await storage.update_data(key, {}) == {"foo": "bar"}
    assert await storage.update_data(key, {"baz": "spam"}) == {
        "foo": "bar",
        "baz": "spam",
    }
    assert await storage.update_data(key, {"baz": "test"}) == {
        "foo": "bar",
        "baz": "test",
    }
    assert await storage.get_data(key) == {"foo": "bar", "baz": "test"}


async def test_memory_storage_close_clears_state_and_data() -> None:
    storage = MemoryStorage()
    key = make_key()

    await storage.set_state(key, State("state", group_name="Group"))
    await storage.set_data(key, {"foo": "bar"})
    await storage.close()

    assert await storage.get_state(key) is None
    assert await storage.get_data(key) == {}


async def test_disabled_event_isolation_does_not_block() -> None:
    isolation = DisabledEventIsolation()
    key = make_key()
    entered = False

    # Повторный захват того же ключа не должен вставать в ожидание.
    async with isolation.lock(key), isolation.lock(key):
        entered = True

    assert entered is True
    await isolation.close()


async def test_simple_event_isolation_serializes_same_key() -> None:
    isolation = SimpleEventIsolation()
    key = make_key()
    order: list[str] = []

    async def worker(name: str) -> None:
        async with isolation.lock(key):
            order.append(f"{name}:start")
            await asyncio.sleep(0)
            order.append(f"{name}:end")

    await asyncio.gather(worker("first"), worker("second"))

    assert order in (
        ["first:start", "first:end", "second:start", "second:end"],
        ["second:start", "second:end", "first:start", "first:end"],
    )

    await isolation.close()
