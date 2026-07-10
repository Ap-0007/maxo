import os
import tempfile

from maxo.dialogs.api.entities import MediaId
from maxo.dialogs.context.media_storage import MediaIdStorage
from maxo.enums import AttachmentType


async def test_get_media_id() -> None:
    manager = MediaIdStorage()
    with tempfile.TemporaryDirectory() as d:
        filename = os.path.join(d, "file_test")  # noqa: PTH118
        media_id = await manager.get_media_id(
            filename,
            None,
            AttachmentType.FILE,
        )
        assert media_id is None

        with open(filename, "w") as file:  # noqa: PTH123
            file.write("test1")

        await manager.save_media_id(
            filename,
            None,
            AttachmentType.FILE,
            MediaId(token="test1"),  # noqa: S106
        )

        media_id = await manager.get_media_id(
            filename,
            None,
            AttachmentType.FILE,
        )
        assert media_id == MediaId(token="test1")  # noqa: S106

        with open(filename, "w") as file:  # noqa: PTH123
            file.write("test2")

        # Хранилище ключуется по st_mtime. Двигаем метку явно, а не спим:
        # разрешение mtime у ФС не гарантировано.
        stat = os.stat(filename)  # noqa: PTH116
        os.utime(filename, (stat.st_atime, stat.st_mtime + 1))

        media_id = await manager.get_media_id(
            filename,
            None,
            AttachmentType.FILE,
        )
        assert media_id is None
