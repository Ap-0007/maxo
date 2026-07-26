import io
from collections.abc import AsyncIterator
from http.cookies import SimpleCookie
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from adaptix import Retort
from aiohttp import ClientSession
from multidict import CIMultiDict
from unihttp.clients.aiohttp import AiohttpAsyncClient
from unihttp.http import HTTPResponse

from maxo.bot.api_client import MaxApiClient, default_transport
from maxo.bot.methods.upload.chunk_upload import _ChunkUpload
from maxo.bot.middlewares import (
    AttachmentNotReadyRetryMiddleware,
    AuthMiddleware,
    NetworkErrorMiddleware,
)
from maxo.errors import (
    MaxBotApiError,
)
from maxo.serialization import create_retort
from maxo.types import AttachmentPayload
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import BufferedInputFile
from tests.constants import TOKEN


def mock_http_response(*chunks: bytes, status: int = 200) -> MagicMock:
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.headers = {}
    mock_response.cookies = {}

    async def chunk_generator() -> AsyncIterator[bytes]:
        for chunk in chunks:
            yield chunk

    mock_response.content.iter_chunked.return_value = chunk_generator()
    return mock_response


@pytest.fixture
async def api_client() -> AsyncIterator[MaxApiClient]:
    retort = create_retort(warming_up=False)
    client = MaxApiClient(
        token=TOKEN,
        transport=default_transport(request_dumper=retort, response_loader=retort),
    )
    yield client
    await client.close()


async def test_api_client_init(api_client: MaxApiClient) -> None:
    assert api_client._token == TOKEN
    assert isinstance(api_client.transport.middleware[0], AuthMiddleware)


async def test_api_client_registers_attachment_retry_middleware(
    api_client: MaxApiClient,
) -> None:
    assert isinstance(
        api_client.transport.middleware[-2],
        AttachmentNotReadyRetryMiddleware,
    )
    assert isinstance(api_client.transport.middleware[-1], NetworkErrorMiddleware)


async def test_api_client_keeps_user_middleware_outer() -> None:
    user_middleware = MagicMock()
    retort = Retort()
    client = MaxApiClient(
        token=TOKEN,
        transport=default_transport(
            request_dumper=retort,
            response_loader=retort,
            middleware=[user_middleware],
        ),
    )
    try:
        assert client.transport.middleware[0] is user_middleware
        assert isinstance(
            client.transport.middleware[-2],
            AttachmentNotReadyRetryMiddleware,
        )
        assert isinstance(client.transport.middleware[-1], NetworkErrorMiddleware)
    finally:
        await client.close()


async def test_upload_resumable_delegates_to_resumable_upload(
    api_client: MaxApiClient,
) -> None:
    result = UploadMediaResult(token="upload-token")  # noqa: S106
    file = BufferedInputFile.file(b"payload", "f.bin")

    with patch(
        "maxo.bot.api_client.resumable_upload",
        new_callable=AsyncMock,
        return_value=result,
    ) as upload_mock:
        assert await api_client.upload_resumable("https://example.com", file) is result

    upload_mock.assert_awaited_once_with(
        url="https://example.com",
        file=file,
        api_client=api_client,
        config=api_client._upload_config,
        size=None,
    )


async def test_custom_transport_is_used_as_is() -> None:
    retort = Retort()
    session = ClientSession()
    transport = AiohttpAsyncClient(
        base_url="https://example.com/",
        request_dumper=retort,
        response_loader=retort,
        session=session,
    )

    client = MaxApiClient(
        token=TOKEN,
        transport=transport,
    )
    try:
        assert client.transport is transport
    finally:
        await client.close()


async def test_chunk_upload_goes_through_auth_middleware(
    api_client: MaxApiClient,
) -> None:
    """upload_resumable шлёт чанки через `transport.call_method`, а не в обход."""
    response = HTTPResponse(
        status_code=200,
        data=b"ok",
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )

    with patch.object(
        AiohttpAsyncClient,
        "make_request",
        new_callable=AsyncMock,
        return_value=response,
    ) as make_request_mock:
        result = await api_client.transport.call_method(
            _ChunkUpload(
                url="https://example.com",
                chunk=b"chunk",
                headers={"Content-Range": "bytes 0-3/4"},
            ),
        )

    assert result is response
    sent_request = make_request_mock.call_args.args[0]
    assert sent_request.method == "POST"
    assert sent_request.raw == b"chunk"
    assert sent_request.header["Authorization"] == TOKEN
    assert sent_request.header["Content-Range"] == "bytes 0-3/4"


def test_api_error_str_uses_fields_and_raw_data() -> None:
    error = MaxBotApiError("code", "error", "message")
    raw_error = MaxBotApiError("", "", "", {"raw": "data"})

    assert str(error) == (
        "MaxBotApiError(code='code', error='error', message='message')"
    )
    assert str(raw_error) == "MaxBotApiError(raw_data={'raw': 'data'})"


async def test_download_to_binaryio(api_client: MaxApiClient) -> None:
    mock_response = mock_http_response(b"test ", b"content")

    with patch(
        "aiohttp.ClientSession.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_request:
        destination = io.BytesIO()
        result = await api_client.download(
            "https://example.com/file",
            destination=destination,
        )

        assert result is destination
        assert destination.read() == b"test content"
        mock_request.assert_called_once()


async def test_download_to_memory_by_default(api_client: MaxApiClient) -> None:
    mock_response = mock_http_response(b"test")

    with patch(
        "aiohttp.ClientSession.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await api_client.download("https://example.com/file")

    assert result is not None
    assert result.read() == b"test"


async def test_download_to_path(api_client: MaxApiClient, tmp_path: Path) -> None:
    mock_response = mock_http_response(b"test ", b"content")

    with patch(
        "aiohttp.ClientSession.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        file_path = tmp_path / "test_file.txt"
        result = await api_client.download(
            "https://example.com/file",
            destination=file_path,
        )

        assert result is None
        assert file_path.read_bytes() == b"test content"


async def test_download_from_attachment_payload(api_client: MaxApiClient) -> None:
    mock_response = mock_http_response(b"test ", b"content")

    with patch(
        "aiohttp.ClientSession.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        payload = AttachmentPayload(url="https://example.com/file")
        destination = io.BytesIO()
        await api_client.download(payload, destination=destination)

        assert destination.read() == b"test content"
