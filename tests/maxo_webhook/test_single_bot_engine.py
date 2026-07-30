import asyncio

import pytest

from maxo import Bot
from maxo.routing.signals import MaxoUpdate
from maxo.transport.webhook.engines.single import SingleBotEngine
from tests.maxo_webhook.fixtures.shutdown import (
    BlockingDispatcher,
    BlockingShutdownDispatcher,
    TrackableTransport,
)
from tests.maxo_webhook.fixtures.web_request import DummyRequest, DummyWebRequest
from tests.maxo_webhook.fixtures.webhook_engine import (
    CapturingAdapter,
    DummyDispatcher,
    DummyRoute,
)


@pytest.mark.asyncio
async def test_single_bot_engine_uses_configured_bot_instead_of_route_params(
    bot: Bot,
    bot_token: str,
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    dispatcher = DummyDispatcher()
    engine = SingleBotEngine(
        dispatcher,
        bot,
        web=adapter,
        route=DummyRoute({"bot_token": "100:OTHER"}),  # ty:ignore[invalid-argument-type]
    )

    response = await engine.handle_request(update_request)
    await asyncio.sleep(0)

    assert response["status_code"] == 200  # ty:ignore[not-subscriptable]
    assert dispatcher.webhook_bot is bot
    assert dispatcher.webhook_bot.token == bot_token
    assert isinstance(dispatcher.webhook_update, MaxoUpdate)
    assert dispatcher.webhook_update.update.message.body.text == "hello"
    assert dispatcher.webhook_update.update.message.body.mid == "msg-1"


@pytest.mark.asyncio
async def test_single_bot_engine_rejects_new_requests_once_shutdown_has_started(
    bot: Bot,
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    dispatcher = BlockingDispatcher()
    engine = SingleBotEngine(
        dispatcher,
        bot,
        web=adapter,
        route=DummyRoute({"bot_token": "100:OTHER"}),  # ty:ignore[invalid-argument-type]
    )

    await engine.handle_request(update_request)
    await asyncio.sleep(0)
    assert dispatcher.started_updates == 1

    shutdown_task = asyncio.create_task(engine.on_shutdown(app=None))  # ty:ignore[invalid-argument-type]
    await asyncio.sleep(0)

    response = await engine.handle_request(
        DummyWebRequest(DummyRequest(json_data={"update_id": 2})),
    )

    dispatcher.release_updates.set()
    await shutdown_task

    assert response["status_code"] == 503  # ty:ignore[not-subscriptable]
    assert dispatcher.started_updates == 1


@pytest.mark.asyncio
async def test_background_engine_rejects_request_during_shutdown(
    bot: Bot,
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    dispatcher = BlockingShutdownDispatcher()
    engine = SingleBotEngine(
        dispatcher,
        bot,
        web=adapter,
        route=DummyRoute({"bot_token": bot.token}),  # ty:ignore[invalid-argument-type]
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
        if engine._task_tracker._tasks:
            await asyncio.wait_for(
                asyncio.gather(*engine._task_tracker._tasks),
                timeout=1,
            )

    assert response["status_code"] == 503  # ty:ignore[not-subscriptable]
    assert dispatcher.background_updates == []
    assert len(engine._task_tracker._tasks) == 0


@pytest.mark.asyncio
async def test_foreground_engine_rejects_request_during_shutdown(
    bot: Bot,
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    dispatcher = BlockingShutdownDispatcher()
    engine = SingleBotEngine(
        dispatcher,
        bot,
        web=adapter,
        route=DummyRoute({"bot_token": bot.token}),  # ty:ignore[invalid-argument-type]
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


@pytest.mark.asyncio
async def test_background_engine_rejects_request_after_shutdown_with_closed_bot_session(
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    transport = TrackableTransport(bot_id=42)
    bot = Bot("42:TEST", client=transport, warming_up=False)
    await bot.start()
    dispatcher = BlockingShutdownDispatcher()
    engine = SingleBotEngine(
        dispatcher,
        bot,
        web=adapter,
        route=DummyRoute({"bot_token": bot.token}),  # ty:ignore[invalid-argument-type]
    )

    dispatcher.release_shutdown.set()
    await engine.on_shutdown(None)  # ty:ignore[invalid-argument-type]

    response = await engine.handle_request(update_request)
    await asyncio.sleep(0)
    dispatcher.background_continue.set()
    if engine._task_tracker._tasks:
        await asyncio.wait_for(asyncio.gather(*engine._task_tracker._tasks), timeout=1)

    # Транспорт создали снаружи - бот его не закрывает, даже при shutdown
    assert transport.closed is False
    assert bot.closed is True
    assert response["status_code"] == 503  # ty:ignore[not-subscriptable]
    assert dispatcher.background_updates == []
    assert dispatcher.background_session_closed == []


@pytest.mark.asyncio
async def test_foreground_engine_rejects_request_after_shutdown_with_closed_bot_session(
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    transport = TrackableTransport(bot_id=42)
    bot = Bot("42:TEST", client=transport)
    await bot.start()
    dispatcher = BlockingShutdownDispatcher()
    engine = SingleBotEngine(
        dispatcher,
        bot,
        web=adapter,
        route=DummyRoute({"bot_token": bot.token}),  # ty:ignore[invalid-argument-type]
    )

    dispatcher.release_shutdown.set()
    await engine.on_shutdown(None)  # ty:ignore[invalid-argument-type]

    response = await engine.handle_request(update_request)

    # Транспорт создали снаружи - бот его не закрывает, даже при shutdown.
    assert transport.closed is False
    assert bot.closed is True
    assert response["status_code"] == 503  # ty:ignore[not-subscriptable]
    assert dispatcher.foreground_updates == []
    assert dispatcher.foreground_session_closed == []
