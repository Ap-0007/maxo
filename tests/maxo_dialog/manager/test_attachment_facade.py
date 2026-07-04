from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maxo import Bot
from maxo.dialogs.api.entities import MediaId
from maxo.dialogs.api.protocols import MediaIdStorageProtocol
from maxo.dialogs.manager.attachment_facade import DialogAttachmentsFacade
from maxo.enums import AttachmentType, UploadType
from maxo.utils.upload_media import FSInputFile


class MockInputFile:
    """Mock InputFile, который не является FSInputFile."""

    def __init__(self) -> None:
        self.type = UploadType.IMAGE

    @property
    def file_name(self) -> str:
        return "mock_file.jpg"

    async def read(self) -> bytes:
        return b"mock data"


@pytest.fixture
def mock_bot() -> Bot:
    return MagicMock(spec=Bot)


@pytest.fixture
def mock_media_storage() -> MediaIdStorageProtocol:
    storage = MagicMock(spec=MediaIdStorageProtocol)
    storage.save_media_id = AsyncMock()
    return storage


async def test_upload_media_with_fs_input_file(
    mock_bot: Bot,
    mock_media_storage: MediaIdStorageProtocol,
) -> None:
    facade = DialogAttachmentsFacade(bot=mock_bot, media_id_storage=mock_media_storage)

    file = FSInputFile(path=Path("/tmp/test.jpg"), type=UploadType.IMAGE)  # noqa: S108

    # Мокаем родительский upload_media, чтобы протестировать только логику сохранения
    with patch(
        "maxo.routing.mixins.attachments.AttachmentsFacade.upload_media",
        new_callable=AsyncMock,
        return_value=(UploadType.IMAGE, "test_token"),
    ):
        result = await facade.upload_media(file)

    assert result == (UploadType.IMAGE, "test_token")

    mock_media_storage.save_media_id.assert_called_once_with(
        path=file.path,
        url=None,
        type=AttachmentType.IMAGE,
        media_id=MediaId(token="test_token"),  # noqa: S106
    )


async def test_upload_media_with_non_fs_input_file(
    mock_bot: Bot,
    mock_media_storage: MediaIdStorageProtocol,
) -> None:
    facade = DialogAttachmentsFacade(bot=mock_bot, media_id_storage=mock_media_storage)

    file = MockInputFile()

    with patch(
        "maxo.routing.mixins.attachments.AttachmentsFacade.upload_media",
        new_callable=AsyncMock,
        return_value=(UploadType.IMAGE, "test_token"),
    ):
        result = await facade.upload_media(file)

    assert result == (UploadType.IMAGE, "test_token")

    # save_media_id НЕ должен вызываться для не-FSInputFile
    mock_media_storage.save_media_id.assert_not_called()


async def test_init(
    mock_bot: Bot,
    mock_media_storage: MediaIdStorageProtocol,
) -> None:
    facade = DialogAttachmentsFacade(bot=mock_bot, media_id_storage=mock_media_storage)

    assert facade._bot == mock_bot
    assert facade._media_id_storage == mock_media_storage
