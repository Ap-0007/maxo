import json
from collections.abc import Iterable
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientConnectionError

from maxo.bot.upload import UploadConfig, UploadMethod, resumable_upload
from maxo.enums import UploadType
from maxo.errors.api import (
    MaxBotApiError,
    MaxBotBadRequestError,
    MaxBotTooManyRequestsError,
    MaxBotUnsupportedMediaTypeError,
)
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import BufferedInputFile

_MIB = 1024 * 1024


class _FakeResponse:
    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    async def read(self) -> bytes:
        return self._body

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None


class _FakeSession:
    def __init__(self, responses: Iterable[_FakeResponse | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def post(
        self,
        url: str,
        data: bytes,
        headers: dict[str, str],
    ) -> _FakeResponse:
        self.calls.append({"url": url, "data": data, "headers": headers})
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class _Retort:
    def load(self, data: Any, tp: type) -> Any:
        return tp(**data)


async def _run(
    session: _FakeSession,
    data: bytes,
    chunk_size: int,
    chunk_retries: int = 3,
) -> UploadMediaResult | None:
    file = BufferedInputFile.file(data, "f.bin")
    return await resumable_upload(
        url="https://upload.example/upload.do",
        file=file,
        session=session,  # type: ignore[arg-type]
        response_loader=_Retort(),
        json_loads=json.loads,
        config=UploadConfig(chunk_size=chunk_size, chunk_retries=chunk_retries),
    )


async def test_sends_chunks_with_correct_content_range() -> None:
    session = _FakeSession(
        [
            _FakeResponse(201, b"0-3/10"),
            _FakeResponse(201, b"0-7/10"),
            _FakeResponse(200, b'{"token": "tok"}'),
        ],
    )

    result = await _run(session, b"abcdefghij", 4)

    assert isinstance(result, UploadMediaResult)
    assert result.token == "tok"  # noqa: S105
    ranges = [call["headers"]["Content-Range"] for call in session.calls]
    assert ranges == ["bytes 0-3/10", "bytes 4-7/10", "bytes 8-9/10"]
    assert [call["data"] for call in session.calls] == [b"abcd", b"efgh", b"ij"]
    assert 'filename="f.bin"' in session.calls[0]["headers"]["Content-Disposition"]


async def test_single_chunk_small_file() -> None:
    session = _FakeSession([_FakeResponse(200, b'{"token": "tok"}')])

    result = await _run(session, b"hello", 1024)

    assert result is not None
    assert result.token == "tok"  # noqa: S105
    assert session.calls[0]["headers"]["Content-Range"] == "bytes 0-4/5"


async def test_non_json_final_body_returns_none() -> None:
    session = _FakeSession([_FakeResponse(200, b"0-4/5")])

    assert await _run(session, b"hello", 1024) is None


async def test_empty_file_raises() -> None:
    session = _FakeSession([])

    with pytest.raises(ValueError, match="пустой файл"):
        await _run(session, b"", 1024)


async def test_client_error_status_raises_without_retry() -> None:
    session = _FakeSession([_FakeResponse(406, b'{"code": "upload.error"}')])

    with pytest.raises(MaxBotApiError):
        await _run(session, b"hello", 1024)

    assert len(session.calls) == 1


@pytest.mark.parametrize(
    ("status", "error_class"),
    [
        (400, MaxBotBadRequestError),
        (415, MaxBotUnsupportedMediaTypeError),
        (429, MaxBotTooManyRequestsError),
    ],
)
async def test_client_error_status_preserves_typed_api_error(
    status: int,
    error_class: type[MaxBotApiError],
) -> None:
    payload = {
        "error_code": "proto.payload",
        "error_data": "attachment.not.ready",
        "message": "cannot process attachment",
    }
    session = _FakeSession([_FakeResponse(status, json.dumps(payload).encode())])

    with pytest.raises(error_class) as exc_info:
        await _run(session, b"hello", 1024)

    error = exc_info.value
    assert error.code == "proto.payload"
    assert error.error == "attachment.not.ready"
    assert error.message == "cannot process attachment"
    assert error.raw_data == payload
    assert len(session.calls) == 1


async def test_server_error_is_retried_then_succeeds() -> None:
    session = _FakeSession(
        [
            _FakeResponse(500, b'{"message": "temporary"}'),
            _FakeResponse(200, b'{"token": "tok"}'),
        ],
    )

    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await _run(session, b"hello", 1024, chunk_retries=3)

    assert result is not None
    assert result.token == "tok"  # noqa: S105
    assert len(session.calls) == 2


async def test_network_error_is_retried_then_reraised() -> None:
    session = _FakeSession(
        [
            ClientConnectionError("boom"),
            ClientConnectionError("boom"),
        ],
    )

    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        pytest.raises(ClientConnectionError),
    ):
        await _run(session, b"hello", 1024, chunk_retries=1)

    assert len(session.calls) == 2


def test_should_use_resumable_respects_explicit_method() -> None:
    assert UploadConfig(method=UploadMethod.RESUMABLE).should_use_resumable(1) is True
    assert UploadConfig(method=UploadMethod.SINGLE).should_use_resumable(10**9) is False


def test_should_use_resumable_auto_by_threshold() -> None:
    config = UploadConfig(method=UploadMethod.AUTO, resumable_threshold=100)
    assert config.should_use_resumable(99) is False
    assert config.should_use_resumable(100) is True


@pytest.mark.parametrize("upload_type", [UploadType.IMAGE, UploadType.VIDEO])
def test_estimated_delay_zero_for_instant_types(upload_type: UploadType) -> None:
    assert UploadConfig().estimated_processing_delay(upload_type, 100 * _MIB) == 0.0


@pytest.mark.parametrize("upload_type", [UploadType.FILE, UploadType.AUDIO])
def test_estimated_delay_grows_with_size(upload_type: UploadType) -> None:
    config = UploadConfig()
    small = config.estimated_processing_delay(upload_type, 1 * _MIB)
    big = config.estimated_processing_delay(upload_type, 100 * _MIB)

    assert small >= config.processing_base_delay
    assert big > small


def test_estimated_delay_is_capped() -> None:
    config = UploadConfig()
    huge = config.estimated_processing_delay(UploadType.FILE, 100_000 * _MIB)

    assert huge == config.processing_max_delay
