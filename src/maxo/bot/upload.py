"""
Загрузка медиа в MAX: настройки, выбор способа и resumable-протокол.

MAX принимает файл двумя способами:

- **single** - обычный multipart-запрос. Простой, но держит весь файл в
  памяти и падает на файлах ~2 ГБ из-за лимита буфера OpenSSL.
- **resumable** - загрузка частями. Файл читается по кускам и отправляется
  последовательными POST-ами, что снимает лимит размера и не держит файл в
  памяти целиком.

Все настройки загрузки собраны в `UploadConfig` (см. `Bot(upload_config=...)`):
способ (`UploadMethod`), размеры/ретраи кусков, ретраи на `attachment.not.ready`
и модель задержки обработки файла на сервере.

Протокол resumable (проверен эмпирически на боевом API):

- Тело запроса - сырые байты куска (`Content-Type: application/octet-stream`),
  не multipart.
- Имя файла передаётся в `Content-Disposition: attachment; filename="..."`.
- Позиция куска - в `Content-Range: bytes {start}-{end}/{total}`.
- Куски должны идти по одному keep-alive соединению: сессия загрузки на
  сервере привязана к соединению (при обрыве - `restore session` ошибка).
- Промежуточный кусок -> HTTP 201 и заголовок `Range: 0-{накоплено}/{total}`.
- Финальный кусок -> HTTP 200. Для `file`/`image` в теле JSON с токеном, для
  `video`/`audio` в теле эхо диапазона (токен берётся из `POST /uploads`).

Через декларативные методы `unihttp` (`MaxoMethod` + `bind_method`) это
реализовать нельзя: у `unihttp` нет маркера сырого тела (`Body` уходит в JSON,
`File` - в multipart), один метод = один запрос, и нет пиннинга соединения.
"""

import asyncio
from collections.abc import Callable
from enum import StrEnum
from typing import Any, Never

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
_SERVER_ERROR_STATUS = 500
_CLIENT_ERROR_STATUS = 400

# Эти типы сервер принимает сразу и обрабатывает асинхронно - ждать не нужно.
_INSTANT_UPLOAD_TYPES = frozenset({UploadType.IMAGE, UploadType.VIDEO})

# Backoff для ретраев на `attachment.not.ready` по умолчанию (см. исследование
# examples/research_upload_delay.py): частые короткие повторы добирают "хвост".
DEFAULT_NOT_READY_BACKOFF = BackoffConfig(
    min_delay=0.2,
    max_delay=3.0,
    factor=1.6,
    jitter=0.1,
)


class UploadMethod(StrEnum):
    """
    Способ загрузки медиа на сервер MAX.

    - `AUTO` - resumable для файлов от `UploadConfig.resumable_threshold`,
      иначе single.
    - `SINGLE` - всегда одним multipart-запросом.
    - `RESUMABLE` - всегда частями (streaming, без лимита ~2 ГБ).
    """

    AUTO = "auto"
    SINGLE = "single"
    RESUMABLE = "resumable"


class UploadConfig(MaxoType):
    """
    Настройки загрузки медиа. Передаётся в `Bot(upload_config=...)`.

    Args:
        method: Способ загрузки (см. `UploadMethod`).
        resumable_threshold: Порог размера (байты), с которого `AUTO` берёт
            resumable.
        chunk_size: Размер куска resumable-загрузки в байтах.
        chunk_retries: Сколько раз повторить отправку куска при временной ошибке.
        chunk_retry_base_delay: Базовая пауза между повторами куска (секунды).
        chunk_retry_max_delay: Максимальная пауза между повторами куска (секунды).
        not_ready_backoff: Backoff для ретраев отправки сообщения при
            `attachment.not.ready`.
        not_ready_max_retries: Максимум таких ретраев.
        processing_base_delay: Базовый сон перед отправкой сообщения (секунды).
        processing_delay_per_mib: Надбавка ко сну за каждый МиБ файла (секунды).
        processing_max_delay: Потолок начального сна (секунды).

    """

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
) -> UploadMediaResult | None:
    """
    Загружает `file` на `url` частями по resumable-протоколу MAX.

    `session` должна быть выделенной keep-alive сессией (одно соединение),
    иначе сервер потеряет сессию загрузки между кусками.

    Возвращает `UploadMediaResult`, если сервер вернул JSON с токеном
    (`file`/`image`), либо `None`, если тело не JSON (`video`/`audio` -
    токен берётся из `POST /uploads`).
    """
    if config is None:
        config = UploadConfig()

    total = await file.size()
    if total <= 0:
        msg = "Нельзя загрузить пустой файл resumable-способом"
        raise ValueError(msg)

    offset = 0
    final_body = b""
    async for chunk in file.stream(config.chunk_size):
        end = offset + len(chunk) - 1
        headers: dict[str, str] = {
            CONTENT_TYPE: _OCTET_STREAM,
            CONTENT_DISPOSITION: f'attachment; filename="{file.file_name}"',
            CONTENT_RANGE: f"bytes {offset}-{end}/{total}",
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
                if response.status < _CLIENT_ERROR_STATUS:
                    return body
                # 5xx повторяем, 4xx - это ошибка запроса, повторять смысла нет.
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
