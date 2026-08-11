import asyncio

import pytest

from maxo.transport.webhook.configs.bot import BotConfig
from maxo.transport.webhook.engines.token import TokenEngine
from tests.maxo_webhook.fixtures.shutdown import (
    BlockingShutdownDispatcher,
    TrackableClient,
)
from tests.maxo_webhook.fixtures.web_request import DummyWebRequest
from tests.maxo_webhook.fixtures.webhook_engine import (
    CapturingAdapter,
    DummyDispatcher,
    DummyRoute,
)


@pytest.mark.asyncio
async def test_token_webhook_engine_dispatches_to_bot_resolved_from_route_token(
    bot_id: int,
    bot_token: str,
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    dispatcher = DummyDispatcher()
    client = TrackableClient(bot_id=bot_id)
    engine = TokenEngine(
        dispatcher,
        web=adapter,
        route=DummyRoute({"bot_token": bot_token}),  # ty:ignore[invalid-argument-type]
        bot_config=BotConfig(client=client),
    )

    response = await engine.handle_request(update_request)
    await asyncio.sleep(0)

    assert response["status_code"] == 200  # ty:ignore[not-subscriptable]
    assert dispatcher.webhook_bot is engine.bots[bot_id]
    assert dispatcher.webhook_bot.token == bot_token
    assert dispatcher.webhook_update is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "route_params",
    [
        {},
        {"bot_token": ""},
    ],
    ids=["missing", "empty"],
)
async def test_token_webhook_engine_returns_not_found_when_route_token_is_missing_or_empty(
    adapter: CapturingAdapter,
    route_params: dict[str, str],
    update_request: DummyWebRequest,
) -> None:
    dispatcher = DummyDispatcher()
    engine = TokenEngine(
        dispatcher,
        web=adapter,
        route=DummyRoute(route_params),  # ty:ignore[invalid-argument-type]
        bot_config=BotConfig(client=TrackableClient()),
    )

    response = await engine.handle_request(update_request)

    assert response == {
        "kind": "json",
        "status_code": 404,
        "data": {"detail": "Not found"},
        "headers": None,
    }
    assert dispatcher.webhook_update is None
    assert engine.bots == {}


@pytest.mark.asyncio
async def test_token_background_engine_rejects_request_during_shutdown_without_creating_bot_or_tracker(
    bot_id: int,
    bot_token: str,
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    dispatcher = BlockingShutdownDispatcher()
    client = TrackableClient(bot_id=bot_id)
    engine = TokenEngine(
        dispatcher,
        web=adapter,
        route=DummyRoute({"bot_token": bot_token}),  # ty:ignore[invalid-argument-type]
        bot_config=BotConfig(client=client),
    )

    shutdown_task = asyncio.create_task(engine.on_shutdown(None))  # ty:ignore[invalid-argument-type]
    await asyncio.wait_for(dispatcher.shutdown_started.wait(), timeout=1)

    try:
        response = await engine.handle_request(update_request)
        await asyncio.sleep(0)
    finally:
        dispatcher.background_continue.set()
        dispatcher.release_shutdown.set()
        await asyncio.wait_for(shutdown_task, timeout=1)
        for tracker in engine._task_trackers.values():
            if tracker._tasks:
                await asyncio.wait_for(asyncio.gather(*tracker._tasks), timeout=1)

    assert response["status_code"] == 503  # ty:ignore[not-subscriptable]
    assert dispatcher.background_updates == []
    assert bot_id not in engine.bots
    assert bot_id not in engine._task_trackers


@pytest.mark.asyncio
async def test_token_foreground_engine_rejects_request_during_shutdown_without_creating_bot(
    bot_id: int,
    bot_token: str,
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    dispatcher = BlockingShutdownDispatcher()
    client = TrackableClient(bot_id=bot_id)
    engine = TokenEngine(
        dispatcher,
        web=adapter,
        route=DummyRoute({"bot_token": bot_token}),  # ty:ignore[invalid-argument-type]
        bot_config=BotConfig(client=client),
    )

    shutdown_task = asyncio.create_task(engine.on_shutdown(None))  # ty:ignore[invalid-argument-type]
    await asyncio.wait_for(dispatcher.shutdown_started.wait(), timeout=1)

    try:
        response = await engine.handle_request(update_request)
    finally:
        dispatcher.release_shutdown.set()
        await asyncio.wait_for(shutdown_task, timeout=1)

    assert response["status_code"] == 503  # ty:ignore[not-subscriptable]
    assert dispatcher.foreground_updates == []
    assert bot_id not in engine.bots
