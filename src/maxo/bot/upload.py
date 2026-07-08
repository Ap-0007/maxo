import asyncio
from collections.abc import Callable
from enum import StrEnum
from typing import Any, Never
from urllib.parse import quote

from aiohttp import ClientError, ClientSession
from aiohttp.hdrs import CONTENT_DISPOSITION, CONTENT_RANGE, CONTENT_TYPE
from unihttp.serialize import ResponseLoader

from maxo.backoff import BackoffConfig
from maxo.enums import UploadType
from maxo.errors import MaxBotApiError
from maxo.errors.api import raise_api_error
from maxo.types import MaxoType
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import InputFile

_MIB = 1024 * 1024
_OCTET_STREAM = "application/octet-stream"
_OK_STATUS = 200
_REDIRECT_STATUS = 300
_SERVER_ERROR_STATUS = 500

_INSTANT_UPLOAD_TYPES = frozenset({UploadType.IMAGE, UploadType.VIDEO})

DEFAULT_NOT_READY_BACKOFF = BackoffConfig(
    min_delay=0.2,
    max_delay=3.0,
    factor=1.6,
    jitter=0.1,
)


class UploadMethod(StrEnum):
    """Способ загрузки медиа на сервер MAX."""

    AUTO = "auto"
    SINGLE = "single"
    RESUMABLE = "resumable"


class UploadConfig(MaxoType):
    """Настройки загрузки медиа для `Bot(upload_config=...)`."""

    method: UploadMethod = UploadMethod.AUTO
    resumable_threshold: int = 20 * _MIB

    chunk_size: int = 10 * _MIB
    chunk_retries: int = 3
    chunk_retry_base_delay: float = 0.5
    chunk_retry_max_delay: float = 5.0

    not_ready_backoff: BackoffConfig = DEFAULT_NOT_READY_BACKOFF
    not_ready_max_retries: int = 10

    processing_base_delay: float = 0.5
    processing_delay_per_mib: float = 0.008
    processing_max_delay: float = 30.0

    def should_use_resumable(self, size: int) -> bool:
        if self.method is UploadMethod.RESUMABLE:
            return True
        if self.method is UploadMethod.SINGLE:
            return False
        return size >= self.resumable_threshold

    def estimated_processing_delay(self, upload_type: UploadType, size: int) -> float:
        if upload_type in _INSTANT_UPLOAD_TYPES:
            return 0.0
        delay = self.processing_base_delay + self.processing_delay_per_mib * (
            size / _MIB
        )
        return min(delay, self.processing_max_delay)


DEFAULT_UPLOAD_CONFIG = UploadConfig()


async def resumable_upload(
    *,
    url: str,
    file: InputFile,
    session: ClientSession,
    response_loader: ResponseLoader,
    json_loads: Callable[[bytes], Any],
    config: UploadConfig | None = None,
    size: int | None = None,
) -> UploadMediaResult | None:
    """
    Загружает файл частями через выделенную keep-alive сессию.

    `size` - заранее известный размер файла в байтах
    """
    if config is None:
        config = UploadConfig()

    if size is None:
        size = await file.size()
    if size <= 0:
        msg = "Нельзя загрузить пустой файл"
        raise ValueError(msg)

    encoded_name = quote(file.file_name, safe="")
    disposition = f'attachment; filename="{encoded_name}"'

    offset = 0
    final_body = b""
    async for chunk in file.stream(config.chunk_size):
        end = offset + len(chunk) - 1
        headers: dict[str, str] = {
            CONTENT_TYPE: _OCTET_STREAM,
            CONTENT_DISPOSITION: disposition,
            CONTENT_RANGE: f"bytes {offset}-{end}/{size}",
        }
        final_body = await _send_chunk(
            session=session,
            url=url,
            chunk=chunk,
            headers=headers,
            config=config,
            json_loads=json_loads,
        )
        offset += len(chunk)

    return _parse_result(final_body, response_loader, json_loads)


async def _send_chunk(
    *,
    session: ClientSession,
    url: str,
    chunk: bytes,
    headers: dict[str, str],
    config: UploadConfig,
    json_loads: Callable[[bytes], Any],
) -> bytes:
    attempt = 0
    while True:
        try:
            async with session.post(url, data=chunk, headers=headers) as response:
                body = await response.read()
                if _OK_STATUS <= response.status < _REDIRECT_STATUS:
                    return body
                # 1xx/3xx/4xx считаем неретраибельными, ретраим только 5xx.
                if (
                    response.status < _SERVER_ERROR_STATUS
                    or attempt >= config.chunk_retries
                ):
                    _raise_upload_error(response.status, body, json_loads)
        except ClientError:
            if attempt >= config.chunk_retries:
                raise

        attempt += 1
        delay = config.chunk_retry_base_delay * 2**attempt
        await asyncio.sleep(min(delay, config.chunk_retry_max_delay))


def _raise_upload_error(
    status: int,
    body: bytes,
    json_loads: Callable[[bytes], Any],
) -> Never:
    code = ""
    message = ""
    raw_data: object = body
    try:
        data = json_loads(body)
    except (ValueError, TypeError):
        message = body.decode("utf-8", "replace")
    else:
        raw_data = data
        if isinstance(data, dict):
            raise_api_error(status, data)
        message = str(data)
    raise MaxBotApiError(
        code=code,
        error=f"upload failed with status {status}",
        message=message,
        raw_data=raw_data,
    )


def _parse_result(
    body: bytes,
    response_loader: ResponseLoader,
    json_loads: Callable[[bytes], Any],
) -> UploadMediaResult | None:
    try:
        data = json_loads(body)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    return response_loader.load(data, UploadMediaResult)
