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


async def test_bot_close() -> None:
    transport = AsyncMock()
    bot = make_bot(client=transport)

    assert bot.client is transport
    assert bot.started is False
    transport.call_method.assert_not_awaited()

    await bot.close()
    assert bot.closed is True
    # Транспорт передали снаружи - закрывать его боту нельзя.
    transport.close.assert_not_awaited()


async def test_bot_context(bot: Bot) -> None:
    with patch("maxo.bot.bot.Bot.close", new_callable=AsyncMock) as mock_close:
        async with bot.context(get_my_info=False):
            pass
        mock_close.assert_awaited_once()


async def test_bot_context_fetches_info_by_default() -> None:
    mock_transport = AsyncMock()
    mock_transport.call_method.return_value = BotInfo(
        user_id=1,
        is_bot=True,
        first_name="Test",
        username="testbot",
        last_activity_time=NOW,
    )
    bot = make_bot(client=mock_transport)

    async with bot.context():
        assert bot.info.user_id == 1

    mock_transport.call_method.assert_awaited_once()


async def test_bot_call_method(bot: Bot) -> None:
    """`call_method` no longer resolves `.info` as a side effect."""
    with patch.object(bot, "_client", MagicMock()) as mock_transport:
        mock_transport.call_method = AsyncMock(return_value="test_result")
        result: object = await bot.call_method(MagicMock())
        assert result == "test_result"
        mock_transport.call_method.assert_awaited_once()
        with pytest.raises(StateError, match="Bot info is not resolved yet"):
            _ = bot.info


async def test_bot_silent_call_method(
    bot: Bot,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with patch.object(bot, "_client", MagicMock()) as mock_transport:
        mock_transport.call_method = AsyncMock(
            side_effect=MockMaxBotApiError("test error"),
        )
        await bot.silent_call_method(MagicMock())
        assert "Failed to make answer" in caplog.text


async def test_bot_download(bot: Bot) -> None:
    downloaded = io.BytesIO(b"downloaded")
    with patch.object(Bot, "download", AsyncMock(return_value=downloaded)) as mock:
        result = await bot.download("https://example.com/file")
        assert result is downloaded
        mock.assert_awaited_once()


async def test_bot_defaults(bot: Bot) -> None:
    assert bot.defaults is not None


async def test_close_on_empty_state_is_noop(bot: Bot) -> None:
    await bot.close()

    assert bot.closed is False


async def test_close_twice_is_noop() -> None:
    bot = make_bot()
    transport = AsyncMock()
    bot._client = transport
    bot._owns_client = True
    bot._info = MagicMock()

    await bot.close()
    await bot.close()

    transport.close.assert_awaited_once()


async def test_bot_async_context_manager() -> None:
    bot = make_bot()

    with patch("maxo.bot.bot.Bot.close", new_callable=AsyncMock) as mock_close:
        async with bot as entered:
            assert entered is bot

    mock_close.assert_awaited_once()


async def test_context_without_auto_close(bot: Bot) -> None:
    with patch("maxo.bot.bot.Bot.close", new_callable=AsyncMock) as mock_close:
        async with bot.context(auto_close=False, get_my_info=False):
            pass

    mock_close.assert_not_awaited()


async def test_bot_upload_media_resumable(bot: Bot) -> None:
    file = BufferedInputFile.file(b"payload", "f.bin")
    upload_result = UploadMediaResult(token="upload-token")  # noqa: S106

    with patch(
        "maxo.bot.bot.resumable_upload",
        new_callable=AsyncMock,
        return_value=upload_result,
    ) as mock_upload:
        result = await bot.upload_media_resumable("https://example.com/upload", file)

    assert result is upload_result
    mock_upload.assert_awaited_once_with(
        bot=bot,
        url="https://example.com/upload",
        file=file,
        size=None,
    )


async def test_client_access_never_hits_network() -> None:
    """Accessing `.client` repeatedly must not touch the network at all."""
    mock_transport = AsyncMock()
    bot = make_bot(client=mock_transport)

    assert bot.client is mock_transport
    assert bot.client is mock_transport

    mock_transport.call_method.assert_not_awaited()


async def test_get_my_info_retries_after_previous_failure() -> None:
    mock_transport = AsyncMock()
    bot = make_bot(client=mock_transport)

    if True:
        mock_transport.call_method.side_effect = MockMaxBotApiError("boom")

        with pytest.raises(MaxBotApiError):
            await bot.get_my_info()

        assert bot.started is False
        with pytest.raises(StateError, match="Bot info is not resolved yet"):
            _ = bot.info

        mock_transport.call_method.side_effect = None
        mock_transport.call_method.return_value = BotInfo(
            user_id=1,
            is_bot=True,
            first_name="Test",
            username="testbot",
            last_activity_time=NOW,
        )

        await bot.get_my_info()
        assert bot.info.user_id == 1


async def test_get_my_info_starts_lazily() -> None:
    mock_transport = AsyncMock()
    bot = make_bot(client=mock_transport)

    if True:
        mock_transport.call_method.return_value = BotInfo(
            user_id=1,
            is_bot=True,
            first_name="Test",
            username="testbot",
            last_activity_time=NOW,
        )

        info = await bot.get_my_info()
        assert info.user_id == 1
        assert bot.started is True


async def test_call_method_does_not_resolve_info() -> None:
    """`bot.send_message(...)` alone must not implicitly resolve `.info` —
    only an explicit `get_my_info()`/`context()` call does that now."""
    mock_transport = AsyncMock()
    bot = make_bot(client=mock_transport)

    mock_transport.call_method.return_value = "ok"

    result: object = await bot.call_method(MagicMock())

    assert result == "ok"
    with pytest.raises(StateError, match="Bot info is not resolved yet"):
        _ = bot.info


async def test_get_my_info_updates_cached_info_directly() -> None:
    """Calling `get_my_info()` on its own (without `start()`) must still
    refresh `.info` — it's the only way it stays consistent with reality."""
    mock_transport = AsyncMock()
    bot = make_bot(client=mock_transport)

    if True:
        mock_transport.call_method.return_value = BotInfo(
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
    mock_transport = AsyncMock()
    bot = make_bot(client=mock_transport)

    if True:
        mock_transport.call_method.return_value = BotInfo(
            user_id=1,
            is_bot=True,
            first_name="Test",
            username="testbot",
            last_activity_time=NOW,
        )

        await bot.get_my_info()
        await bot.get_my_info()

        assert mock_transport.call_method.await_count == 2
