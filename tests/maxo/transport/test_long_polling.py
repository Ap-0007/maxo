import asyncio
import signal
import sys
from asyncio import CancelledError
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import ANY, AsyncMock, call, patch

import pytest
from adaptix.load_error import LoadError

from maxo.bot.api_client import MaxApiClient
from maxo.bot.bot import Bot
from maxo.bot.methods import GetUpdates
from maxo.bot.state import RunningBotState
from maxo.omit import Omitted
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.signals.update import MaxoUpdate
from maxo.transport.long_polling import LongPolling
from maxo.types import BotInfo, MaxoType, UpdateList
from maxo.types.updates import Updates
from tests.factories import make_bot


@dataclass
class MockUpdate(MaxoType):
    timestamp: int = field(default=0)


@pytest.fixture
def mock_api_client() -> AsyncMock:
    return AsyncMock(spec=MaxApiClient)


@pytest.fixture
def mock_bot(mock_api_client: AsyncMock) -> Bot:
    bot = make_bot()
    bot._state = RunningBotState(
        info=BotInfo(
            user_id=123,
            first_name="test_bot",
            username="test_bot",
            is_bot=True,
            last_activity_time=datetime.fromtimestamp(1234567890, tz=UTC),
        ),
        api_client=mock_api_client,
    )
    return bot


@pytest.fixture
def mock_feed_max_update() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_dispatcher(mock_feed_max_update: AsyncMock) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.feed_max_update = mock_feed_max_update  # type: ignore[method-assign]
    return dispatcher


@pytest.fixture
def long_polling(mock_dispatcher: Dispatcher) -> LongPolling:
    return LongPolling(dispatcher=mock_dispatcher)


async def anext_coro(generator: AsyncIterator[Any]) -> Any:
    return await anext(generator)


async def run_generator_once(generator: AsyncIterator[Any]) -> None:
    task = asyncio.create_task(anext_coro(generator))
    await asyncio.sleep(0.1)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


async def test_handles_load_error_and_skips_update(
    long_polling: LongPolling,
    mock_bot: Bot,
    mock_api_client: AsyncMock,
) -> None:
    initial_marker = 10
    mock_api_client.call_method.side_effect = [
        LoadError("Test LoadError"),
        UpdateList(
            updates=cast(list[Updates], [MockUpdate(timestamp=100)]),
            marker=initial_marker + 2,
        ),
        CancelledError,
    ]

    with (
        patch("maxo.transport.long_polling.loggers.dispatcher") as mock_logger,
        patch("maxo.backoff.Backoff.next") as mock_backoff_next,
        patch(
            "maxo.backoff.Backoff.sleep",
            new_callable=AsyncMock,
        ) as mock_backoff_sleep,
    ):
        updates_generator = long_polling._get_updates(
            bot=mock_bot,
            marker=initial_marker,
        )

        first_yielded_update = await updates_generator.__anext__()

        mock_logger.exception.assert_called_once_with(
            "Ошибка загрузки апдейта в модель. "
            "Сообщите об этой ошибке в https://github.com/K1rL3s/maxo/issues",
        )
        assert mock_api_client.call_method.call_count == 2
        mock_api_client.call_method.assert_has_calls(
            [
                call(
                    GetUpdates(
                        limit=100,
                        marker=initial_marker,
                        timeout=30,
                        types=Omitted(),
                    ),
                ),
                call(
                    GetUpdates(
                        limit=100,
                        marker=initial_marker + 1,
                        timeout=30,
                        types=Omitted(),
                    ),
                ),
            ],
        )

        assert isinstance(first_yielded_update, MaxoUpdate)
        assert isinstance(first_yielded_update.update, MockUpdate)
        assert first_yielded_update.update.timestamp == 100
        assert first_yielded_update.marker == initial_marker + 2

        mock_backoff_next.assert_not_called()
        mock_backoff_sleep.assert_not_called()

        with pytest.raises(CancelledError):
            await updates_generator.__anext__()


async def test_handles_load_error_with_no_marker(
    long_polling: LongPolling,
    mock_bot: Bot,
    mock_api_client: AsyncMock,
) -> None:
    mock_api_client.call_method.side_effect = [
        LoadError("Test LoadError"),
        CancelledError,
    ]

    with (
        patch("maxo.transport.long_polling.loggers.dispatcher") as mock_logger,
        patch("maxo.backoff.Backoff.next") as mock_backoff_next,
        patch(
            "maxo.backoff.Backoff.sleep",
            new_callable=AsyncMock,
        ) as mock_backoff_sleep,
    ):
        updates_generator = long_polling._get_updates(bot=mock_bot, marker=None)

        with pytest.raises(CancelledError):
            await updates_generator.__anext__()

        mock_logger.exception.assert_called_once_with(
            "Ошибка загрузки апдейта в модель. "
            "Сообщите об этой ошибке в https://github.com/K1rL3s/maxo/issues",
        )
        assert mock_api_client.call_method.call_count == 2
        mock_backoff_next.assert_called_once()
        mock_backoff_sleep.assert_called_once()


async def test_handles_general_exception(
    long_polling: LongPolling,
    mock_bot: Bot,
    mock_api_client: AsyncMock,
    mock_feed_max_update: AsyncMock,
) -> None:
    mock_api_client.call_method.side_effect = ValueError(
        "Test ValueError",
    )

    with patch("maxo.transport.long_polling.loggers.dispatcher") as mock_logger:
        updates_generator = long_polling._get_updates(bot=mock_bot)

        await run_generator_once(updates_generator)

        mock_logger.exception.assert_called_once_with(
            "Failed to fetch updates - %s: %s",
            "ValueError",
            ANY,
        )
        mock_api_client.call_method.assert_called_once()
        mock_feed_max_update.assert_not_called()


@pytest.mark.parametrize(
    "types",
    [Omitted(), []],
    ids=["omitted", "empty-list"],
)
async def test_start_collects_used_updates_when_types_not_given(
    mock_bot: Bot,
    types: Any,
) -> None:
    # Пустой список, как и Omitted(), означает "посчитать по роутерам",
    # иначе бот молча перестаёт получать апдейты
    dispatcher = Dispatcher()

    @dispatcher.message_created()
    async def _handler(update: Any) -> None: ...

    long_polling = LongPolling(dispatcher=dispatcher)

    async def empty_updates(**_kwargs: Any) -> AsyncIterator[Any]:
        return
        yield  # pragma: no cover

    with patch.object(long_polling, "_get_updates", side_effect=empty_updates) as spy:
        await long_polling.start(mock_bot, types=types, auto_close_bot=False)

    assert spy.call_args.kwargs["types"] == ["message_created"]


async def test_start_respects_explicit_types(mock_bot: Bot) -> None:
    dispatcher = Dispatcher()

    @dispatcher.message_created()
    async def _handler(update: Any) -> None: ...

    long_polling = LongPolling(dispatcher=dispatcher)

    async def empty_updates(**_kwargs: Any) -> AsyncIterator[Any]:
        return
        yield  # pragma: no cover

    with patch.object(long_polling, "_get_updates", side_effect=empty_updates) as spy:
        await long_polling.start(
            mock_bot,
            types=["bot_started"],
            auto_close_bot=False,
        )

    assert spy.call_args.kwargs["types"] == ["bot_started"]


async def test_consume_updates_waits_for_running_handlers_on_stop(
    mock_dispatcher: Dispatcher,
    mock_bot: Bot,
) -> None:
    """Остановка graceful: уже запущенный хендлер добегает до конца."""
    long_polling = LongPolling(dispatcher=mock_dispatcher)
    stop_event = asyncio.Event()
    handled: list[Any] = []
    handler_started = asyncio.Event()

    async def slow_feed(update: MaxoUpdate[Any], bot: Bot | None = None) -> Any:
        handler_started.set()
        await asyncio.sleep(0.05)
        handled.append(update)

    mock_dispatcher.feed_max_update = slow_feed  # type: ignore[method-assign]

    async def updates() -> AsyncIterator[MaxoUpdate[Any]]:
        yield MaxoUpdate(update=cast(Updates, MockUpdate(timestamp=1)), marker=1)
        # Имитируем висящий долгий поллинг: новых апдейтов нет.
        await asyncio.sleep(3600)
        yield MaxoUpdate(  # pragma: no cover
            update=cast(Updates, MockUpdate(timestamp=2)),
            marker=2,
        )

    consumer = asyncio.create_task(
        long_polling._consume_updates(
            bot=mock_bot,
            updates_poller=updates(),
            stop_event=stop_event,
        ),
    )

    await handler_started.wait()
    stop_event.set()
    await asyncio.wait_for(consumer, timeout=1)

    assert len(handled) == 1


async def test_consume_updates_stops_on_exhausted_poller(
    mock_dispatcher: Dispatcher,
    mock_bot: Bot,
    mock_feed_max_update: AsyncMock,
) -> None:
    long_polling = LongPolling(dispatcher=mock_dispatcher)

    async def updates() -> AsyncIterator[MaxoUpdate[Any]]:
        yield MaxoUpdate(update=cast(Updates, MockUpdate(timestamp=1)), marker=1)

    await asyncio.wait_for(
        long_polling._consume_updates(
            bot=mock_bot,
            updates_poller=updates(),
            stop_event=asyncio.Event(),
        ),
        timeout=1,
    )

    mock_feed_max_update.assert_awaited_once()


async def test_consume_updates_does_not_start_when_already_stopped(
    mock_dispatcher: Dispatcher,
    mock_bot: Bot,
    mock_feed_max_update: AsyncMock,
) -> None:
    long_polling = LongPolling(dispatcher=mock_dispatcher)
    stop_event = asyncio.Event()
    stop_event.set()

    async def updates() -> AsyncIterator[MaxoUpdate[Any]]:
        yield MaxoUpdate(  # pragma: no cover
            update=cast(Updates, MockUpdate(timestamp=1)),
            marker=1,
        )

    await asyncio.wait_for(
        long_polling._consume_updates(
            bot=mock_bot,
            updates_poller=updates(),
            stop_event=stop_event,
        ),
        timeout=1,
    )

    mock_feed_max_update.assert_not_awaited()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="loop.add_signal_handler не поддерживается на Windows",
)
async def test_signal_handler_sets_stop_event(long_polling: LongPolling) -> None:
    stop_event = asyncio.Event()

    remove_signal_handlers = long_polling._add_signal_handlers(stop_event)
    try:
        signal.raise_signal(signal.SIGTERM)
        # Сигнал доезжает до loop через self-pipe, одного тика цикла мало.
        await asyncio.wait_for(stop_event.wait(), timeout=1)

        assert stop_event.is_set()
    finally:
        remove_signal_handlers()


async def test_signal_handlers_not_installed_when_disabled(
    long_polling: LongPolling,
    mock_bot: Bot,
) -> None:
    async def empty_updates(**_kwargs: Any) -> AsyncIterator[Any]:
        return
        yield  # pragma: no cover

    with (
        patch.object(long_polling, "_get_updates", side_effect=empty_updates),
        patch.object(long_polling, "_add_signal_handlers") as add_signal_handlers,
    ):
        await long_polling.start(
            mock_bot,
            auto_close_bot=False,
            handle_signals=False,
        )

    add_signal_handlers.assert_not_called()
