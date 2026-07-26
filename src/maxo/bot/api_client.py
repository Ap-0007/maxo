import io
import json
import pathlib
import ssl
from collections.abc import Callable
from typing import Any, BinaryIO

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from anyio import open_file
from unihttp.bind_method import bind_method
from unihttp.clients.aiohttp import AiohttpAsyncClient
from unihttp.clients.base import BaseAsyncClient
from unihttp.http.stream import AsyncChunkStream
from unihttp.method import StreamMethod
from unihttp.middlewares import AsyncMiddleware
from unihttp.serialize import RequestDumper, ResponseLoader

from maxo.bot.methods.download import Download
from maxo.bot.middlewares import (
    AttachmentNotReadyRetryMiddleware,
    AuthMiddleware,
    NetworkErrorMiddleware,
)
from maxo.bot.upload import UploadConfig, resumable_upload
from maxo.types import AttachmentPayload
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import InputFile

_CA_CERT_PATH = (pathlib.Path(__file__).parent / "russiantrustedca.pem").resolve()


def default_transport(
    *,
    request_dumper: RequestDumper,
    response_loader: ResponseLoader,
    base_url: str = "https://platform-api2.max.ru/",
    middleware: list[AsyncMiddleware] | None = None,
    ssl_context: ssl.SSLContext | None = None,
    json_dumps: Callable[[Any], str] = json.dumps,
    json_loads: Callable[[str | bytes | bytearray], Any] = json.loads,
    limit: int | None = None,
    timeout: ClientTimeout | None = None,
) -> AiohttpAsyncClient:
    if ssl_context is None:
        ssl_context = ssl.create_default_context()
        ssl_context.load_verify_locations(cafile=_CA_CERT_PATH)

    connector = (
        TCPConnector(ssl=ssl_context)
        if limit is None
        else TCPConnector(ssl=ssl_context, limit=limit)
    )
    session = (
        ClientSession(connector=connector)
        if timeout is None
        else ClientSession(connector=connector, timeout=timeout)
    )
    return AiohttpAsyncClient(
        base_url=base_url,
        request_dumper=request_dumper,
        response_loader=response_loader,
        middleware=middleware or [],
        session=session,
        json_dumps=json_dumps,
        json_loads=json_loads,
    )


class MaxApiClient:
    def __init__(
        self,
        token: str,
        transport: BaseAsyncClient,
        upload_config: UploadConfig | None = None,
    ) -> None:
        self._token = token

        if upload_config is None:
            upload_config = UploadConfig()
        self._upload_config = upload_config

        not_ready_retry = AttachmentNotReadyRetryMiddleware(
            max_retries=self._upload_config.not_ready_max_retries,
            backoff_config=self._upload_config.not_ready_backoff,
        )
        transport.middleware.extend(
            [AuthMiddleware(self._token), not_ready_retry, NetworkErrorMiddleware()],
        )
        self.transport = transport

    async def call_method_stream(  # for unihttp bind_method
        self,
        method: StreamMethod,
    ) -> AsyncChunkStream:
        return await self.transport.call_method_stream(method)

    _download_stream = bind_method(Download)

    async def upload_resumable(
        self,
        url: str,
        file: InputFile,
        size: int | None = None,
    ) -> UploadMediaResult | None:
        """
        Загружает файл частями, без чтения всего файла в память.

        `size` - заранее известный размер файла, чтобы не делать лишний `stat`.
        """
        return await resumable_upload(
            url=url,
            file=file,
            api_client=self,
            config=self._upload_config,
            size=size,
        )

    async def close(self) -> None:
        await self.transport.close()

    async def download(
        self,
        url: str | AttachmentPayload,
        destination: BinaryIO | pathlib.Path | str | None = None,
        chunk_size: int = 65536,
        seek: bool = True,
    ) -> BinaryIO | None:
        """Скачивает вложение чанками, без буферизации ответа в память."""
        if isinstance(url, AttachmentPayload):
            url = url.url

        async with await self._download_stream(
            url=url,
            __chunk_size__=chunk_size,
        ) as stream:
            if isinstance(destination, (str, pathlib.Path)):
                async with await open_file(destination, "wb") as f:
                    async for chunk in stream:
                        await f.write(chunk)
                return None
            # binary_io
            binary_io = destination if destination is not None else io.BytesIO()
            async for chunk in stream:
                binary_io.write(chunk)
            if seek:
                binary_io.seek(0)
            return binary_io
