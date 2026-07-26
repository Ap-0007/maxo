import asyncio
from typing import Any

from unihttp.clients.base import BaseAsyncClient

from tests.maxo_webhook.fixtures.webhook_engine import DummyDispatcher


class BlockingShutdownDispatcher(DummyDispatcher):
    def __init__(self) -> None:
        super().__init__()
        self.shutdown_started = asyncio.Event()
        self.release_shutdown = asyncio.Event()
        self.foreground_updates: list[dict[str, Any]] = []
        self.background_updates: list[dict[str, Any]] = []
        self.foreground_session_closed: list[bool | None] = []
        self.background_session_closed: list[bool | None] = []
        self.background_continue = asyncio.Event()

    async def emit_shutdown(self, **kwargs: Any) -> None:
        self.shutdown_started.set()
        await self.release_shutdown.wait()

    async def feed_webhook_update(self, bot: Any, update: dict[str, Any]) -> None:
        self.foreground_updates.append(update)
        self.foreground_session_closed.append(getattr(bot.session, "closed", None))

    async def feed_raw_update(self, bot: Any, update: dict[str, Any]) -> None:
        self.background_updates.append(update)
        self.background_session_closed.append(getattr(bot.session, "closed", None))
        await self.background_continue.wait()


class BlockingDispatcher(DummyDispatcher):
    """Test dispatcher that blocks raw update handling until released."""

    def __init__(self) -> None:
        super().__init__()
        self.started_updates = 0
        self.release_updates = asyncio.Event()

    async def feed_raw_update(self, bot, update):
        self.started_updates += 1
        self.webhook_bot = bot
        self.webhook_update = update
        await self.release_updates.wait()
        return self.result

    async def emit_shutdown(self, **kwargs):
        return None


class TrackableSession(BaseAsyncClient):
    """Fake unihttp transport that tracks whether it was closed."""

    def __init__(self) -> None:
        super().__init__(base_url="", request_dumper=None, response_loader=None)  # type: ignore[arg-type]
        self.closed = False

    async def close(self) -> None:
        self.closed = True
