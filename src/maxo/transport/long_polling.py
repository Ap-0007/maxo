import asyncio
import contextlib
import signal
import time
from collections.abc import AsyncIterator, Callable, Iterator, Sequence
from types import FrameType
from typing import Any

from adaptix.load_error import LoadError

from maxo import loggers
from maxo.backoff import Backoff, BackoffConfig
from maxo.bot.bot import Bot
from maxo.omit import Omittable, Omitted, is_defined
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.signals.shutdown import AfterShutdown, BeforeShutdown
from maxo.routing.signals.startup import AfterStartup, BeforeStartup
from maxo.routing.signals.update import MaxoUpdate
from maxo.routing.utils import collect_used_updates

_DEFAULT_BACKOFF_CONFIG = BackoffConfig(
    min_delay=1.0,
    max_delay=5.0,
    factor=1.3,
    jitter=0.1,
)

_STOP_SIGNALS = (signal.SIGINT, signal.SIGTERM)

# То же, что приватный `signal._HANDLER`.
_SignalHandler = Callable[[int, FrameType | None], Any] | int | None


class LongPolling:
    def __init__(
        self,
        dispatcher: Dispatcher,
        backoff_config: BackoffConfig = _DEFAULT_BACKOFF_CONFIG,
    ) -> None:
        self._dispatcher = dispatcher
        self._backoff_config = backoff_config
        self._lock = asyncio.Lock()

    def run(
        self,
        bot: Bot,
        timeout: Omittable[int] = 30,
        limit: Omittable[int] = 100,
        marker: Omittable[int | None] = Omitted(),
        types: Omittable[Sequence[str]] = Omitted(),
        auto_close_bot: bool = True,
        drop_pending_updates: bool = False,
        handle_signals: bool = True,
        **workflow_data: Any,
    ) -> None:
        asyncio.run(
            self.start(
                bot=bot,
                timeout=timeout,
                limit=limit,
                marker=marker,
                types=types,
                auto_close_bot=auto_close_bot,
                drop_pending_updates=drop_pending_updates,
                handle_signals=handle_signals,
                **workflow_data,
            ),
        )

    async def start(
        self,
        bot: Bot,
        timeout: Omittable[int] = 30,
        limit: Omittable[int] = 100,
        marker: Omittable[int | None] = Omitted(),
        types: Omittable[Sequence[str]] = Omitted(),
        auto_close_bot: bool = True,
        drop_pending_updates: bool = False,
        handle_signals: bool = True,
        **workflow_data: Any,
    ) -> None:
        dispatcher = self._dispatcher
        used_types: list[str] = list(
            types if is_defined(types) and types else collect_used_updates(dispatcher),
        )

        async with self._lock:
            dispatcher.workflow_data.update(bot=bot, **workflow_data)

            await dispatcher.feed_signal(BeforeStartup(), bot)

            async with bot.context(auto_close=auto_close_bot):
                loggers.dispatcher.info(
                    "Polling started for @%s id=%s",
                    bot.state.info.username,
                    bot.state.info.user_id,
                )

                await dispatcher.feed_signal(AfterStartup(), bot)

                updates_poller = self._get_updates(
                    bot=bot,
                    timeout=timeout,
                    limit=limit,
                    marker=marker,
                    types=used_types,
                    drop_pending_updates=drop_pending_updates,
                )

                stop_event = asyncio.Event()

                with (
                    self._signal_handlers(stop_event, enabled=handle_signals),
                    contextlib.suppress(KeyboardInterrupt),
                ):
                    await self._consume_updates(
                        bot=bot,
                        updates_poller=updates_poller,
                        stop_event=stop_event,
                    )

                await dispatcher.feed_signal(BeforeShutdown(), bot)

                loggers.dispatcher.info(
                    "Polling stop for @%s bot id=%s",
                    bot.state.info.username,
                    bot.state.info.user_id,
                )

        await dispatcher.feed_signal(AfterShutdown())

    async def _consume_updates(
        self,
        bot: Bot,
        updates_poller: AsyncIterator[MaxoUpdate[Any]],
        stop_event: asyncio.Event,
    ) -> None:
        """
        Раздает апдейты хендлерам, пока не попросят остановиться.

        По сигналу остановки новые апдейты больше не забираются, а выход из
        `TaskGroup` дожидается уже запущенных хендлеров.
        """
        dispatcher = self._dispatcher

        async with asyncio.TaskGroup() as tg:
            async for update in self._iter_until_stop(updates_poller, stop_event):
                # Задача отслеживается TaskGroup, ссылка не нужна.
                tg.create_task(  # type: ignore[unused-awaitable]
                    dispatcher.feed_max_update(update, bot),
                )

    async def _iter_until_stop(
        self,
        updates_poller: AsyncIterator[MaxoUpdate[Any]],
        stop_event: asyncio.Event,
    ) -> AsyncIterator[MaxoUpdate[Any]]:
        """
        Отдает апдейты, пока не выставлен `stop_event`.

        Ожидание апдейта гонится с событием остановки, чтобы не висеть в
        `get_updates` до конца его таймаута.
        """
        stop_waiter = asyncio.ensure_future(stop_event.wait())
        update_waiter: asyncio.Future[MaxoUpdate[Any]] | None = None

        try:
            while not stop_event.is_set():
                update_waiter = asyncio.ensure_future(anext(updates_poller))
                done, _ = await asyncio.wait(
                    (update_waiter, stop_waiter),
                    return_when=asyncio.FIRST_COMPLETED,
                )

                if update_waiter not in done:
                    loggers.dispatcher.info(
                        "Получен сигнал остановки, "
                        "новые апдейты больше не забираются",
                    )
                    break

                try:
                    update = update_waiter.result()
                except StopAsyncIteration:
                    break
                finally:
                    update_waiter = None

                yield update
        finally:
            stop_waiter.cancel()
            # Незавершенный `get_updates` надо погасить здесь: `asyncio.wait`
            # не отменяет ожидаемое, а сессия бота закроется сразу после нас.
            if update_waiter is not None:
                update_waiter.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await update_waiter

    @contextlib.contextmanager
    def _signal_handlers(
        self,
        stop_event: asyncio.Event,
        *,
        enabled: bool = True,
    ) -> Iterator[None]:
        """
        Перехватывает SIGINT и SIGTERM, пока идет поллинг.

        На выходе возвращает прежние обработчики: `remove_signal_handler`
        сбрасывает сигнал в дефолт и затер бы чужой обработчик, в том числе
        тот, которым `asyncio.run` гасит главную задачу по Ctrl+C.
        """
        if not enabled:
            yield
            return

        loop = asyncio.get_running_loop()
        previous: list[tuple[signal.Signals, _SignalHandler]] = []

        for sig in _STOP_SIGNALS:
            handler = signal.getsignal(sig)
            try:
                loop.add_signal_handler(sig, stop_event.set)
            except (NotImplementedError, RuntimeError) as error:
                # NotImplementedError - Windows не умеет add_signal_handler,
                # RuntimeError - set_wakeup_fd работает только в главном потоке.
                loggers.dispatcher.warning(
                    "Сигнал %s не перехватывается: %s",
                    sig.name,
                    error,
                )
                continue

            previous.append((sig, handler))

        try:
            yield
        finally:
            for sig, handler in previous:
                loop.remove_signal_handler(sig)
                if handler is not None:
                    signal.signal(sig, handler)

    async def _get_updates(
        self,
        bot: Bot,
        timeout: Omittable[int] = 30,
        limit: Omittable[int] = 100,
        marker: Omittable[int | None] = Omitted(),
        types: Omittable[list[str]] = Omitted(),
        drop_pending_updates: bool = False,
    ) -> AsyncIterator[MaxoUpdate[Any]]:
        start_time = time.time()
        backoff = Backoff(self._backoff_config)
        bot_id = bot.state.info.user_id
        bot_username = bot.state.info.username

        failed = False
        while True:
            try:
                result = await bot.get_updates(
                    limit=limit,
                    timeout=timeout,
                    marker=marker,
                    types=types,
                )
            except LoadError:
                loggers.dispatcher.exception(
                    "Ошибка загрузки апдейта в модель. "
                    "Сообщите об этой ошибке в https://github.com/K1rL3s/maxo/issues",
                )
                if is_defined(marker):
                    marker += 1
                    continue

                failed = True
                backoff.next()
                loggers.dispatcher.warning(
                    "Первый запрос на получение обновлений не удался. "
                    "Sleep for %f seconds and try again... "
                    "(tryings = %d, username = @%s, bot id = %d)",
                    backoff.current_delay,
                    backoff.counter,
                    bot_username,
                    bot_id,
                )
                await backoff.sleep()
                continue
            except Exception as exception:  # noqa: BLE001
                failed = True
                loggers.dispatcher.exception(
                    "Failed to fetch updates - %s: %s",
                    type(exception).__name__,
                    exception,
                )
                backoff.next()
                loggers.dispatcher.warning(
                    "Sleep for %f seconds and try again... "
                    "(tryings = %d, username = @%s, bot id = %d)",
                    backoff.current_delay,
                    backoff.counter,
                    bot_username,
                    bot_id,
                )
                await backoff.sleep()
                continue

            if failed:
                loggers.dispatcher.info(
                    "Connection established "
                    "(tryings = %d, username = @%s, bot id = %d)",
                    backoff.counter,
                    bot_username,
                    bot_id,
                )
                backoff.reset()
                failed = False

            marker = result.marker

            for update in result.updates:
                if drop_pending_updates and update.timestamp.timestamp() < start_time:
                    loggers.long_polling.debug("Skip pending update: %s", update)
                    continue
                loggers.long_polling.debug("New update: %s", update)
                yield MaxoUpdate(update=update, marker=result.marker)
