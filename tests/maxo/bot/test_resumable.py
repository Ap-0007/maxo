import json
from collections.abc import Iterable
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientConnectionError

from maxo.bot.resumable import resumable_upload
from maxo.errors.api import MaxBotApiError
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import BufferedInputFile


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
    """Мок сессии: отдаёт заранее заданные ответы и пишет заголовки вызовов."""

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
    **kwargs: Any,
) -> UploadMediaResult | None:
    file = BufferedInputFile.file(data, "f.bin")
    return await resumable_upload(
        url="https://upload.example/upload.do",
        file=file,
        session=session,  # type: ignore[arg-type]
        response_loader=_Retort(),
        json_loads=json.loads,
        chunk_size=chunk_size,
        **kwargs,
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
    # Тело каждого запроса - соответствующий кусок.
    assert [call["data"] for call in session.calls] == [b"abcd", b"efgh", b"ij"]
    # Имя файла уходит в Content-Disposition.
    assert 'filename="f.bin"' in session.calls[0]["headers"]["Content-Disposition"]


async def test_single_chunk_small_file() -> None:
    session = _FakeSession([_FakeResponse(200, b'{"token": "tok"}')])

    result = await _run(session, b"hello", 1024)

    assert result is not None
    assert result.token == "tok"  # noqa: S105
    assert session.calls[0]["headers"]["Content-Range"] == "bytes 0-4/5"


async def test_non_json_final_body_returns_none() -> None:
    # video/audio возвращают эхо диапазона - не JSON.
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

    # Изначальная попытка + 1 ретрай.
    assert len(session.calls) == 2
