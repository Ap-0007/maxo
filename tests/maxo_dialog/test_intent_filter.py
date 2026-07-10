from typing import Any

from maxo.dialogs.api.entities import Context
from maxo.dialogs.api.internal import CONTEXT_KEY
from maxo.dialogs.context.intent_filter import IntentFilter
from maxo.fsm import State, StatesGroup


class SG(StatesGroup):
    first = State()


class Other(StatesGroup):
    first = State()


def make_context(state: State) -> Context:
    return Context(
        _intent_id="i",
        _stack_id="s",
        state=state,
        start_data={},
        widget_data={},
        dialog_data={},
    )


async def test_passes_when_group_is_none() -> None:
    assert await IntentFilter(None)(object(), {}) is True  # type: ignore[arg-type]


async def test_rejects_without_context() -> None:
    assert await IntentFilter(SG)(object(), {}) is False  # type: ignore[arg-type]


async def test_accepts_matching_group() -> None:
    ctx: dict[Any, Any] = {CONTEXT_KEY: make_context(SG.first)}

    assert await IntentFilter(SG)(object(), ctx) is True  # type: ignore[arg-type]


async def test_rejects_other_group() -> None:
    ctx: dict[Any, Any] = {CONTEXT_KEY: make_context(Other.first)}

    assert await IntentFilter(SG)(object(), ctx) is False  # type: ignore[arg-type]
