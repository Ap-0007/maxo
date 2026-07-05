"""
Resumable-загрузка медиа в MAX.

MAX поддерживает загрузку файла частями (chunked / resumable). В отличие от
обычного multipart-запроса, который держит весь файл в памяти и отправляется
одним HTTP-вызовом (и падает на файлах ~2 ГБ из-за лимита буфера OpenSSL),
resumable читает файл по кускам и отправляет их последовательными POST-ами.

Протокол (проверен эмпирически на боевом API):

- Тело запроса - сырые байты куска (`Content-Type: application/octet-stream`),
  не multipart.
- Имя файла передаётся в `Content-Disposition: attachment; filename="..."`.
- Позиция куска - в `Content-Range: bytes {start}-{end}/{total}`.
- Куски должны идти по одному keep-alive соединению: сессия загрузки на
  сервере привязана к соединению (при обрыве - `restore session` ошибка).
- Промежуточный кусок -> HTTP 201 и заголовок `Range: 0-{накоплено}/{total}`.
- Финальный кусок -> HTTP 200. Для `file`/`image` в теле JSON с токеном, для
  `video`/`audio` в теле эхо диапазона (токен берётся из `POST /uploads`).
"""

import asyncio
from collections.abc import Callable
from typing import Any, Never

from aiohttp import ClientError, ClientSession
from unihttp.serialize import ResponseLoader

from maxo.errors import MaxBotApiError
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import InputFile

# 10 МиБ - компромисс между числом запросов и памятью на один кусок.
DEFAULT_UPLOAD_CHUNK_SIZE = 10 * 1024 * 1024
# Сколько раз повторить отправку куска при временной ошибке.
DEFAULT_UPLOAD_CHUNK_RETRIES = 3

_OCTET_STREAM = "application/octet-stream"
_RETRY_BASE_DELAY = 0.5
_RETRY_MAX_DELAY = 5.0
_SERVER_ERROR_STATUS = 500
_CLIENT_ERROR_STATUS = 400


async def resumable_upload(
    *,
    url: str,
    file: InputFile,
    session: ClientSession,
    response_loader: ResponseLoader,
    json_loads: Callable[[bytes], Any],
    chunk_size: int = DEFAULT_UPLOAD_CHUNK_SIZE,
    chunk_retries: int = DEFAULT_UPLOAD_CHUNK_RETRIES,
) -> UploadMediaResult | None:
    """
    Загружает `file` на `url` частями по resumable-протоколу MAX.

    `session` должна быть выделенной keep-alive сессией (одно соединение),
    иначе сервер потеряет сессию загрузки между кусками.

    Возвращает `UploadMediaResult`, если сервер вернул JSON с токеном
    (`file`/`image`), либо `None`, если тело не JSON (`video`/`audio` -
    токен берётся из `POST /uploads`).
    """
    total = await file.size()
    if total <= 0:
        msg = "Нельзя загрузить пустой файл resumable-способом"
        raise ValueError(msg)

    offset = 0
    final_body = b""
    async for chunk in file.stream(chunk_size):
        end = offset + len(chunk) - 1
        headers = {
            "Content-Type": _OCTET_STREAM,
            "Content-Disposition": f'attachment; filename="{file.file_name}"',
            "Content-Range": f"bytes {offset}-{end}/{total}",
        }
        final_body = await _send_chunk(
            session=session,
            url=url,
            chunk=chunk,
            headers=headers,
            retries=chunk_retries,
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
    retries: int,
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
                if response.status < _SERVER_ERROR_STATUS or attempt >= retries:
                    _raise_upload_error(response.status, body, json_loads)
        except ClientError:
            if attempt >= retries:
                raise

        attempt += 1
        await asyncio.sleep(min(_RETRY_BASE_DELAY * 2**attempt, _RETRY_MAX_DELAY))


def _raise_upload_error(
    status: int,
    body: bytes,
    json_loads: Callable[[bytes], Any],
) -> Never:
    code = ""
    message = ""
    try:
        data = json_loads(body)
    except (ValueError, TypeError):
        message = body[:200].decode("utf-8", "replace")
    else:
        if isinstance(data, dict):
            code = str(data.get("code", ""))
            message = str(data.get("message", ""))
    raise MaxBotApiError(code, f"upload failed with status {status}", message)


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
