from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maxo.dialogs.api.internal import CONTEXT_KEY, STACK_KEY, STORAGE_KEY
from maxo.dialogs.context.intent_middleware import IntentErrorMiddleware
from maxo.routing.middlewares.fsm_context import FSM_STORAGE_KEY


class RecordingProxy:
    """Пишет порядок вызовов, чтобы проверить, что unlock идёт последним."""

    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self.user_id = 1

    async def save_context(self, context: Any) -> None:
        self.calls.append("save_context")

    async def save_stack(self, stack: Any) -> None:
        self.calls.append("save_stack")

    async def unlock(self) -> None:
        self.calls.append("unlock")


async def run_middleware(*, stack_empty: bool) -> list[str]:
    calls: list[str] = []
    proxy = RecordingProxy(calls)

    middleware = IntentErrorMiddleware(
        registry=MagicMock(),
        access_validator=MagicMock(is_allowed=AsyncMock(return_value=True)),
        events_isolation=MagicMock(),
    )
    middleware._is_error_supported = MagicMock(return_value=True)  # type: ignore[method-assign]
    middleware._load_stack = AsyncMock(  # type: ignore[method-assign]
        return_value=MagicMock(empty=MagicMock(return_value=stack_empty)),
    )
    middleware._load_last_context = AsyncMock(return_value=MagicMock())  # type: ignore[method-assign]

    ctx: dict[Any, Any] = {FSM_STORAGE_KEY: MagicMock()}
    with (
        patch(
            "maxo.dialogs.context.intent_middleware.event_context_from_error",
            return_value=MagicMock(),
        ),
        patch(
            "maxo.dialogs.context.intent_middleware.StorageProxy",
            return_value=proxy,
        ),
    ):
        await middleware(MagicMock(), ctx, AsyncMock())  # type: ignore[arg-type]

    assert ctx[STORAGE_KEY] is proxy
    assert STACK_KEY in ctx
    assert CONTEXT_KEY in ctx
    return calls


async def test_saves_context_and_stack_before_unlock() -> None:
    calls = await run_middleware(stack_empty=False)

    # unlock строго последним: иначе параллельный апдейт того же пользователя
    # захватит лок и прочитает ещё не сохранённые context/stack
    assert calls == ["save_context", "save_stack", "unlock"]


async def test_saves_stack_before_unlock_without_context() -> None:
    calls = await run_middleware(stack_empty=True)

    assert calls == ["save_stack", "unlock"]


@pytest.mark.parametrize("stack_empty", [True, False])
async def test_unlock_is_always_last(stack_empty: bool) -> None:
    calls = await run_middleware(stack_empty=stack_empty)

    assert calls[-1] == "unlock"
    assert "unlock" not in calls[:-1]
