from contextlib import aclosing
from enum import StrEnum
from typing import TYPE_CHECKING
from urllib.parse import quote

from maxo.backoff import BackoffConfig
from maxo.bot.methods.upload.chunk_upload import UploadResponseBody, _ChunkUpload
from maxo.bot.middlewares import ChunkUploadRetryMiddleware
from maxo.enums import UploadType
from maxo.errors import MaxBotApiError
from maxo.errors.api import raise_api_error
from maxo.serialization import get_retort
from maxo.types import BaseMaxoType
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import InputFile

if TYPE_CHECKING:
    from maxo.bot.bot import Bot

_MIB = 1024 * 1024
_CLIENT_ERROR_STATUS = 400

_INSTANT_UPLOAD_TYPES = frozenset({UploadType.IMAGE, UploadType.VIDEO})

DEFAULT_NOT_READY_BACKOFF = BackoffConfig(
    min_delay=0.2,
    max_delay=3.0,
    factor=1.6,
    jitter=0.1,
)
DEFAULT_CHUNK_BACKOFF = BackoffConfig(
    min_delay=0.5,
    max_delay=5.0,
    factor=2.0,
    jitter=0.1,
)


class UploadMethod(StrEnum):
    """Способ загрузки медиа на сервер MAX."""

    AUTO = "auto"
    SINGLE = "single"
    RESUMABLE = "resumable"


class UploadConfig(BaseMaxoType):
    """Настройки загрузки медиа для `Bot(upload_config=...)`."""

    method: UploadMethod = UploadMethod.AUTO
    resumable_threshold: int = 50 * _MIB

    chunk_size: int = 50 * _MIB
    chunk_retries: int = 3
    chunk_backoff: BackoffConfig = DEFAULT_CHUNK_BACKOFF

    not_ready_backoff: BackoffConfig = DEFAULT_NOT_READY_BACKOFF
    not_ready_max_retries: int = 10

    processing_base_delay: float = 0.5
    processing_delay_per_mib: float = 0.008
    processing_max_delay: float = 30.0

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("`chunk_size` should be greater than 0")
        if self.chunk_retries < 0:
            raise ValueError("`chunk_retries` should not be negative")
        if self.not_ready_max_retries < 0:
            raise ValueError("`not_ready_max_retries` should not be negative")
        if self.resumable_threshold < 0:
            raise ValueError("`resumable_threshold` should not be negative")
        if self.processing_base_delay < 0:
            raise ValueError("`processing_base_delay` should not be negative")
        if self.processing_delay_per_mib < 0:
            raise ValueError("`processing_delay_per_mib` should not be negative")
        if self.processing_max_delay < 0:
            raise ValueError("`processing_max_delay` should not be negative")

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


async def resumable_upload(
    bot: "Bot",
    url: str,
    file: InputFile,
    size: int | None = None,
) -> UploadMediaResult | None:
    """
    Загружает файл частями через `bot`.

    `size` - заранее известный размер файла в байтах
    """
    config = bot.upload_config

    if size is None:
        size = await file.size()
    if size <= 0:
        msg = "Нельзя загрузить пустой файл"
        raise ValueError(msg)

    encoded_name = quote(file.file_name, safe="")
    disposition = f'attachment; filename="{encoded_name}"'

    offset = 0
    final_body: UploadResponseBody = b""
    # aclosing: при ошибке `async for` не закрывает генератор, а у
    # `FSInputFile.stream` внутри него остаётся открытый файл.
    async with aclosing(file.stream(config.chunk_size)) as chunks:
        async for chunk in chunks:
            end = offset + len(chunk) - 1
            headers: dict[str, str] = {
                "Content-Type": "application/octet-stream",
                "Content-Disposition": disposition,
                "Content-Range": f"bytes {offset}-{end}/{size}",
            }
            response = await bot.call_method(
                _ChunkUpload(url=url, chunk=chunk, headers=headers),
                middleware=[
                    ChunkUploadRetryMiddleware(
                        max_retries=config.chunk_retries,
                        backoff_config=config.chunk_backoff,
                    ),
                ],
            )
            body = response.data
            if response.status_code < _CLIENT_ERROR_STATUS:
                final_body = body
            elif isinstance(body, dict):
                raise_api_error(response.status_code, body)
            else:
                raise MaxBotApiError(
                    code="",
                    error=f"upload failed with status {response.status_code}",
                    message=body.decode("utf-8", "replace")
                    if isinstance(body, bytes)
                    else str(body or ""),
                    raw_data=body,
                )

            offset += len(chunk)

    if offset != size:
        # Файл изменился между замером размера и чтением
        msg = f"Размер файла изменился во время загрузки: {size} -> {offset} байт"
        raise ValueError(msg)

    if not isinstance(final_body, dict):
        return None
    return get_retort().load(final_body, UploadMediaResult)
