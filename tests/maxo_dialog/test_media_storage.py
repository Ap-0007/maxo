import os
from pathlib import Path

from maxo.dialogs.api.entities import MediaId
from maxo.dialogs.context.media_storage import MediaIdStorage
from maxo.enums import AttachmentType

TYPE = AttachmentType.IMAGE


async def test_get_media_id_without_path_and_url() -> None:
    storage = MediaIdStorage()

    assert await storage.get_media_id(path=None, url=None, type=TYPE) is None


async def test_save_media_id_without_path_and_url_is_noop() -> None:
    storage = MediaIdStorage()

    await storage.save_media_id(
        path=None,
        url=None,
        type=TYPE,
        media_id=MediaId(token="tok"),  # noqa: S106,
    )

    assert len(storage.cache) == 0


async def test_save_and_get_by_url() -> None:
    storage = MediaIdStorage()
    media_id = MediaId(token="tok")  # noqa: S106

    await storage.save_media_id(
        path=None,
        url="http://e.com",
        type=TYPE,
        media_id=media_id,
    )

    assert (
        await storage.get_media_id(path=None, url="http://e.com", type=TYPE) == media_id
    )


async def test_get_media_id_missing_from_cache() -> None:
    storage = MediaIdStorage()

    assert await storage.get_media_id(path=None, url="http://e.com", type=TYPE) is None


async def test_save_and_get_by_path(tmp_path: Path) -> None:
    file = tmp_path / "pic.png"
    file.write_bytes(b"a")
    storage = MediaIdStorage()
    media_id = MediaId(token="tok")  # noqa: S106

    await storage.save_media_id(path=file, url=None, type=TYPE, media_id=media_id)

    assert await storage.get_media_id(path=file, url=None, type=TYPE) == media_id


async def test_cache_invalidated_when_file_changed(tmp_path: Path) -> None:
    file = tmp_path / "pic.png"
    file.write_bytes(b"a")
    storage = MediaIdStorage()
    await storage.save_media_id(
        path=file,
        url=None,
        type=TYPE,
        media_id=MediaId(token="tok"),  # noqa: S106,
    )

    stat = file.stat()
    os.utime(file, (stat.st_atime, stat.st_mtime + 100))

    assert await storage.get_media_id(path=file, url=None, type=TYPE) is None


async def test_missing_file_keeps_cached_media_id(tmp_path: Path) -> None:
    file = tmp_path / "pic.png"
    file.write_bytes(b"a")
    storage = MediaIdStorage()
    media_id = MediaId(token="tok")  # noqa: S106
    await storage.save_media_id(path=file, url=None, type=TYPE, media_id=media_id)

    file.unlink()

    # mtime неизвестен - считаем кэш валидным
    assert await storage.get_media_id(path=file, url=None, type=TYPE) == media_id
