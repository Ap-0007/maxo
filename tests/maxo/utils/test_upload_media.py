from pathlib import Path

from maxo.enums import UploadType
from maxo.utils.upload_media import BufferedInputFile, FSInputFile


async def test_buffered_input_file_factories() -> None:
    cases = [
        (BufferedInputFile.image, UploadType.IMAGE),
        (BufferedInputFile.video, UploadType.VIDEO),
        (BufferedInputFile.audio, UploadType.AUDIO),
        (BufferedInputFile.file, UploadType.FILE),
    ]

    for factory, upload_type in cases:
        input_file = factory(b"payload", "file.bin")

        assert input_file.file_name == "file.bin"
        assert input_file.type is upload_type
        assert await input_file.read() == b"payload"


async def test_fs_input_file_factories(tmp_path: Path) -> None:
    path = tmp_path / "file.bin"
    path.write_bytes(b"payload")

    cases = [
        (FSInputFile.image, UploadType.IMAGE),
        (FSInputFile.video, UploadType.VIDEO),
        (FSInputFile.audio, UploadType.AUDIO),
        (FSInputFile.file, UploadType.FILE),
    ]

    for factory, upload_type in cases:
        input_file = factory(path)

        assert input_file.path == path
        assert input_file.file_name == "file.bin"
        assert input_file.type is upload_type
        assert await input_file.read() == b"payload"


async def test_fs_input_file_custom_name(tmp_path: Path) -> None:
    path = tmp_path / "file.bin"
    path.write_bytes(b"payload")
    input_file = FSInputFile.image(path, file_name="custom.bin")

    assert input_file.file_name == "custom.bin"
