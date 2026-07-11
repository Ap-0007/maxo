from pathlib import Path

from maxo.enums import UploadType
from maxo.utils.upload_media import BufferedInputFile, FSInputFile, InputFile


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


async def test_buffered_input_file_size() -> None:
    input_file = BufferedInputFile.file(b"payload", "file.bin")

    assert await input_file.size() == len(b"payload")


async def test_fs_input_file_size(tmp_path: Path) -> None:
    path = tmp_path / "file.bin"
    path.write_bytes(b"x" * 123)
    input_file = FSInputFile.file(path)

    assert await input_file.size() == 123


async def test_input_file_default_size_reads_content() -> None:
    class CustomInputFile(InputFile):
        @property
        def file_name(self) -> str:
            return "custom.bin"

        @property
        def type(self) -> UploadType:
            return UploadType.FILE

        async def read(self) -> bytes:
            return b"payload"

    assert await CustomInputFile().size() == len(b"payload")


async def _collect(input_file: InputFile, chunk_size: int) -> list[bytes]:
    return [chunk async for chunk in input_file.stream(chunk_size)]


async def test_buffered_input_file_stream() -> None:
    input_file = BufferedInputFile.file(b"abcdefghij", "f.bin")

    assert await _collect(input_file, 4) == [b"abcd", b"efgh", b"ij"]


async def test_buffered_input_file_stream_whole_when_chunk_large() -> None:
    input_file = BufferedInputFile.file(b"abcdefghij", "f.bin")

    assert await _collect(input_file, 100) == [b"abcdefghij"]


async def test_fs_input_file_stream(tmp_path: Path) -> None:
    path = tmp_path / "f.bin"
    path.write_bytes(b"abcdefghij")
    input_file = FSInputFile.file(path)

    assert await _collect(input_file, 4) == [b"abcd", b"efgh", b"ij"]


async def test_input_file_default_stream_reads_content() -> None:
    class CustomInputFile(InputFile):
        @property
        def file_name(self) -> str:
            return "custom.bin"

        @property
        def type(self) -> UploadType:
            return UploadType.FILE

        async def read(self) -> bytes:
            return b"abcdefghij"

    assert await _collect(CustomInputFile(), 4) == [b"abcd", b"efgh", b"ij"]
