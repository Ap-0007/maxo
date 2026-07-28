import asyncio
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maxo.bot.bot import Bot
from maxo.bot.upload import UploadConfig, UploadMethod
from maxo.errors import MaxBotApiError
from maxo.errors.state import StateError
from maxo.types import BotInfo
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import BufferedInputFile
from tests.constants import NOW, TOKEN
from tests.factories import make_bot


class MockMaxBotApiError(MaxBotApiError):
    def __init__(self, message: str, code: str = "", error: str = "") -> None:
        self.message = message
        self.code = code
        self.error = error


@pytest.fixture
def bot() -> Bot:
    return make_bot()


async def test_bot_init(bot: Bot) -> None:
    assert bot.token == TOKEN
    assert bot.started is False
    assert bot.closed is False
    with pytest.raises(StateError, match="Not started bot"):
        _ = bot.api_client
    with pytest.raises(StateError, match="Bot info is not resolved yet"):
        _ = bot.info


def test_default_upload_config_is_not_shared() -> None:
    first = make_bot()
    second = make_bot()

    first.upload_config.method = UploadMethod.SINGLE

    assert second.upload_config.method is UploadMethod.AUTO
    assert first.upload_config is not second.upload_config


def test_explicit_upload_config_is_preserved() -> None:
    config = UploadConfig(method=UploadMethod.RESUMABLE)
    bot = make_bot(upload_config=config)

    assert bot.upload_config is config


async def test_bot_start_and_close() -> None:
    bot = make_bot()
    assert bot.started is False

    with patch("maxo.bot.bot.MaxApiClient") as mock_api_client_class:
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value = mock_api_client
        mock_api_client.closed = False
        mock_api_client.transport.call_method.return_value = BotInfo(
            user_id=1,
            is_bot=True,
            first_name="Test",
            username="testbot",
            last_activity_time=NOW,
        )

        async def _mark_closed() -> None:
            mock_api_client.closed = True

        mock_api_client.close.side_effect = _mark_closed

        await bot.start()
        assert bot.started is True
        assert bot.info.user_id == 1
        mock_api_client.transport.call_method.assert_awaited_once()

        await bot.close()
        assert bot.closed is True
        mock_api_client.close.assert_awaited_once()


async def test_bot_context(bot: Bot) -> None:
    with patch("maxo.bot.bot.Bot.close", new_callable=AsyncMock) as mock_close:
        async with bot.context():
            pass
        mock_close.assert_awaited_once()


async def test_bot_call_method(bot: Bot) -> None:
    bot._info = MagicMock()  # уже "started" — call_method не должен звать start()
    with patch.object(bot, "_api_client", MagicMock()) as mock_api_client:
        mock_api_client.transport.call_method = AsyncMock(
            return_value="test_result",
        )
        result: object = await bot.call_method(MagicMock())
        assert result == "test_result"
        mock_api_client.transport.call_method.assert_awaited_once()


async def test_bot_silent_call_method(
    bot: Bot,
    caplog: pytest.LogCaptureFixture,
) -> None:
    bot._info = MagicMock()
    with patch.object(bot, "_api_client", MagicMock()) as mock_api_client:
        mock_api_client.transport.call_method = AsyncMock(
            side_effect=MockMaxBotApiError("test error"),
        )
        await bot.silent_call_method(MagicMock())
        assert "Failed to make answer" in caplog.text


async def test_bot_download(bot: Bot) -> None:
    downloaded = io.BytesIO(b"downloaded")
    bot._info = MagicMock()
    with patch.object(bot, "_api_client", MagicMock()) as mock_api_client:
        mock_api_client.download = AsyncMock(return_value=downloaded)
        result = await bot.download("https://example.com/file")
        assert result is downloaded
        mock_api_client.download.assert_awaited_once()


async def test_bot_defaults_and_retort(bot: Bot) -> None:
    assert bot.retort is not None
    assert bot.defaults is not None


async def test_close_on_empty_state_is_noop(bot: Bot) -> None:
    await bot.close()

    assert bot.closed is False


async def test_close_twice_is_noop() -> None:
    bot = make_bot()
    api_client = AsyncMock()
    api_client.closed = False

    async def _mark_closed() -> None:
        api_client.closed = True

    api_client.close.side_effect = _mark_closed
    bot._api_client = api_client
    bot._info = MagicMock()

    await bot.close()
    await bot.close()

    api_client.close.assert_awaited_once()


async def test_bot_async_context_manager() -> None:
    bot = make_bot()

    with patch("maxo.bot.bot.Bot.close", new_callable=AsyncMock) as mock_close:
        async with bot as entered:
            assert entered is bot

    mock_close.assert_awaited_once()


async def test_context_without_auto_close(bot: Bot) -> None:
    with patch("maxo.bot.bot.Bot.close", new_callable=AsyncMock) as mock_close:
        async with bot.context(auto_close=False):
            pass

    mock_close.assert_not_awaited()


async def test_bot_upload_media_resumable(bot: Bot) -> None:
    file = BufferedInputFile.file(b"payload", "f.bin")
    upload_result = UploadMediaResult(token="upload-token")  # noqa: S106

    bot._info = MagicMock()
    with patch.object(bot, "_api_client", MagicMock()) as mock_api_client:
        mock_api_client.upload_resumable = AsyncMock(return_value=upload_result)
        result = await bot.upload_media_resumable("https://example.com/upload", file)

    assert result is upload_result
    mock_api_client.upload_resumable.assert_awaited_once_with(
        "https://example.com/upload",
        file,
        None,
    )


async def test_start_caches_info() -> None:
    bot = make_bot()

    with patch("maxo.bot.bot.MaxApiClient") as mock_api_client_class:
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value = mock_api_client
        mock_api_client.transport.call_method.return_value = BotInfo(
            user_id=1,
            is_bot=True,
            first_name="Test",
            username="testbot",
            last_activity_time=NOW,
        )

        await bot.start()
        info = bot.info
        await bot.start()
        again = bot.info

        assert info is again
        mock_api_client.transport.call_method.assert_awaited_once()


async def test_start_retries_info_after_previous_failure() -> None:
    bot = make_bot()

    with patch("maxo.bot.bot.MaxApiClient") as mock_api_client_class:
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value = mock_api_client
        mock_api_client.transport.call_method.side_effect = MockMaxBotApiError("boom")

        with pytest.raises(MaxBotApiError):
            await bot.start()

        assert bot.started is True
        with pytest.raises(StateError, match="Bot info is not resolved yet"):
            _ = bot.info

        mock_api_client.transport.call_method.side_effect = None
        mock_api_client.transport.call_method.return_value = BotInfo(
            user_id=1,
            is_bot=True,
            first_name="Test",
            username="testbot",
            last_activity_time=NOW,
        )

        await bot.start()
        assert bot.info.user_id == 1


async def test_get_my_info_starts_lazily() -> None:
    bot = make_bot()

    with patch("maxo.bot.bot.MaxApiClient") as mock_api_client_class:
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value = mock_api_client
        mock_api_client.transport.call_method.return_value = BotInfo(
            user_id=1,
            is_bot=True,
            first_name="Test",
            username="testbot",
            last_activity_time=NOW,
        )

        info = await bot.get_my_info()
        assert info.user_id == 1
        assert bot.started is True


async def test_call_method_starts_lazily_and_resolves_info() -> None:
    """Exact scenario: `bot.send_message(...)` then `bot.info`, without ever
    calling `start()` explicitly — both must work, not just the send."""
    bot = make_bot()

    with patch("maxo.bot.bot.MaxApiClient") as mock_api_client_class:
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value = mock_api_client
        info = BotInfo(
            user_id=1,
            is_bot=True,
            first_name="Test",
            username="testbot",
            last_activity_time=NOW,
        )
        mock_api_client.transport.call_method.side_effect = [info, "ok"]

        result: object = await bot.call_method(MagicMock())

        assert result == "ok"
        assert bot.info is info


async def test_get_my_info_waits_for_lock() -> None:
    """`get_my_info` must actually respect `_lock`, not just check
    `_api_client is None` — otherwise concurrent first calls could each
    build their own transport/session and leak one."""
    bot = make_bot()

    async with bot._lock:
        task = asyncio.create_task(bot.get_my_info())
        await asyncio.sleep(0)
        assert not task.done()


async def test_start_waits_for_lock() -> None:
    """`start` must respect `_lock` — otherwise concurrent first calls would
    each make a redundant `get_my_info` network call."""
    bot = make_bot()

    async with bot._lock:
        task = asyncio.create_task(bot.start())
        await asyncio.sleep(0)
        assert not task.done()


async def test_get_my_info_updates_cached_info_directly() -> None:
    """Calling `get_my_info()` on its own (without `start()`) must still
    refresh `.info` — it's the only way it stays consistent with reality."""
    bot = make_bot()

    with patch("maxo.bot.bot.MaxApiClient") as mock_api_client_class:
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value = mock_api_client
        mock_api_client.transport.call_method.return_value = BotInfo(
            user_id=1,
            is_bot=True,
            first_name="Test",
            username="testbot",
            last_activity_time=NOW,
        )

        info = await bot.get_my_info()

        assert bot.info is info


async def test_get_my_info_always_hits_network() -> None:
    """Unlike `start()`, repeated `get_my_info()` calls must not be cached —
    it's the "give me fresh data now" escape hatch."""
    bot = make_bot()

    with patch("maxo.bot.bot.MaxApiClient") as mock_api_client_class:
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value = mock_api_client
        mock_api_client.transport.call_method.return_value = BotInfo(
            user_id=1,
            is_bot=True,
            first_name="Test",
            username="testbot",
            last_activity_time=NOW,
        )

        await bot.get_my_info()
        await bot.get_my_info()

        assert mock_api_client.transport.call_method.await_count == 2
