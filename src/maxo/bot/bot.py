import io
import pathlib
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from types import TracebackType
from typing import BinaryIO, Self, TypeVar

from anyio import open_file
from unihttp.bind_method import bind_method
from unihttp.clients.base import BaseAsyncClient
from unihttp.http.response import HTTPResponse
from unihttp.http.stream import AsyncChunkStream
from unihttp.method import BaseMethod, ResponseType, StreamMethod
from unihttp.middlewares import AsyncMiddleware

from maxo import loggers
from maxo.bot.client import default_client
from maxo.bot.defaults import BotDefaults, apply_defaults
from maxo.bot.methods import (
    AddMembers,
    AnswerOnCallback,
    DeleteAdmin,
    DeleteChat,
    DeleteMessage,
    EditBotInfo,
    EditChat,
    EditMessage,
    EditMyCommands,
    GetAdmins,
    GetChat,
    GetChatByLink,
    GetChats,
    GetMembers,
    GetMembership,
    GetMessageById,
    GetMessages,
    GetMyInfo,
    GetPinnedMessage,
    GetSubscriptions,
    GetUpdates,
    GetUploadUrl,
    GetVideoAttachmentDetails,
    LeaveChat,
    PinMessage,
    RemoveMember,
    SendAction,
    SendMessage,
    SetAdmins,
    Subscribe,
    UnpinMessage,
    Unsubscribe,
    UploadMedia,
)
from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.download import Download
from maxo.bot.middlewares import (
    AttachmentNotReadyRetryMiddleware,
    AuthMiddleware,
    NetworkErrorMiddleware,
)
from maxo.bot.upload import UploadConfig, resumable_upload
from maxo.bot.warming_up import warm_up
from maxo.errors import MaxBotApiError
from maxo.errors.state import StateError
from maxo.types import AttachmentPayload, BotInfo, MaxoType
from maxo.types.binding import bind_bot
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import InputFile

_MethodResultT = TypeVar("_MethodResultT", bound=MaxoType)


class Bot(BaseAsyncClient):  # BaseAsyncClient for mypy
    def __init__(
        self,
        token: str,
        *,
        defaults: BotDefaults | None = None,
        upload_config: UploadConfig | None = None,
        warming_up: bool = True,
        client: BaseAsyncClient | None = None,
        middlewares: Sequence[AsyncMiddleware] = (),
    ) -> None:
        self._defaults = defaults or BotDefaults()
        self._token = token
        self._upload_config = (
            upload_config if upload_config is not None else UploadConfig()
        )

        self.middleware: list[AsyncMiddleware] = [
            *middlewares,
            AuthMiddleware(self._token),
            AttachmentNotReadyRetryMiddleware(
                max_retries=self._upload_config.not_ready_max_retries,
                backoff_config=self._upload_config.not_ready_backoff,
            ),
            NetworkErrorMiddleware(),
        ]
        self._client = client

        self._owns_client = client is None
        self._closed = False

        if warming_up:
            warm_up()

        self._info: BotInfo | None = None

    @property
    def client(self) -> BaseAsyncClient:
        if self._client is None:
            self._client = default_client()
        return self._client

    @property
    def info(self) -> BotInfo:
        if self._info is None:
            raise StateError("Bot info is not resolved yet")
        return self._info

    @property
    def started(self) -> bool:
        return self._info is not None

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def defaults(self) -> BotDefaults:
        return self._defaults

    @property
    def upload_config(self) -> UploadConfig:
        return self._upload_config

    @property
    def token(self) -> str:
        return self._token

    @asynccontextmanager
    async def context(
        self,
        auto_close: bool = True,
        get_my_info: bool = True,
    ) -> AsyncIterator[Self]:
        try:
            if get_my_info:
                await self.get_my_info()
            yield self
        finally:
            if auto_close:
                await self.close()

    async def get_my_info(self) -> BotInfo:
        info = await self.client.call_method(GetMyInfo(), middleware=self.middleware)
        self._info = bind_bot(info, self)
        return self._info

    async def close(self) -> None:
        if self._closed or self._client is None:
            return
        self._closed = True

        if self._owns_client:
            await self._client.close()

    async def call_method(  # for unihttp bind_method
        self,
        method: BaseMethod[ResponseType],
        *,
        middleware: Sequence[AsyncMiddleware] | None = None,
    ) -> ResponseType:
        method = apply_defaults(method, self._defaults)
        result = await self.client.call_method(
            method,
            middleware=[*self.middleware, *(middleware or ())],
        )
        return bind_bot(result, self)

    async def call_method_stream(  # for unihttp bind_method
        self,
        method: StreamMethod,
        *,
        middleware: Sequence[AsyncMiddleware] | None = None,
    ) -> HTTPResponse[AsyncChunkStream]:
        return await self.client.call_method_stream(
            method,
            middleware=[*self.middleware, *(middleware or ())],
        )

    async def silent_call_method(self, method: MaxoMethod[_MethodResultT]) -> None:
        try:
            await self.call_method(method)
        except MaxBotApiError as e:
            # Webhook-ответ не позволяет вернуть ошибку вызывающему коду.
            loggers.bot.error("Failed to make answer: %s: %s", e.__class__.__name__, e)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

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

        response = await self.call_method_stream(
            Download(url=url, __chunk_size__=chunk_size),
        )
        async with response.data as stream:
            if isinstance(destination, (str, pathlib.Path)):
                async with await open_file(destination, "wb") as file:
                    async for chunk in stream:
                        await file.write(chunk)
                return None

            binary_io = destination if destination is not None else io.BytesIO()
            async for chunk in stream:
                binary_io.write(chunk)
            if seek:
                binary_io.seek(0)
            return binary_io

    async def upload_media_resumable(
        self,
        upload_url: str,
        file: InputFile,
        size: int | None = None,
    ) -> UploadMediaResult | None:
        """
        Загружает медиа по `upload_url` частями.

        `size` - заранее известный размер файла, чтобы не делать лишний `stat`.
        """
        return await resumable_upload(bot=self, url=upload_url, file=file, size=size)

    # Bots
    edit_bot_info = bind_method(EditBotInfo)
    edit_my_commands = bind_method(EditMyCommands)

    # Chats
    add_members = bind_method(AddMembers)
    delete_admin = bind_method(DeleteAdmin)
    delete_chat = bind_method(DeleteChat)
    edit_chat = bind_method(EditChat)
    get_admins = bind_method(GetAdmins)
    get_chat = bind_method(GetChat)
    get_chat_by_link = bind_method(GetChatByLink)
    get_chats = bind_method(GetChats)
    get_members = bind_method(GetMembers)
    get_membership = bind_method(GetMembership)
    get_pinned_message = bind_method(GetPinnedMessage)
    leave_chat = bind_method(LeaveChat)
    pin_message = bind_method(PinMessage)
    remove_member = bind_method(RemoveMember)
    send_action = bind_method(SendAction)
    set_admins = bind_method(SetAdmins)
    unpin_message = bind_method(UnpinMessage)

    # Messages
    answer_on_callback = bind_method(AnswerOnCallback)
    delete_message = bind_method(DeleteMessage)
    edit_message = bind_method(EditMessage)
    get_message_by_id = bind_method(GetMessageById)
    get_messages = bind_method(GetMessages)
    get_video_attachment_details = bind_method(GetVideoAttachmentDetails)
    send_message = bind_method(SendMessage)

    # Subscriptions
    get_subscriptions = bind_method(GetSubscriptions)
    get_updates = bind_method(GetUpdates)
    subscribe = bind_method(Subscribe)
    unsubscribe = bind_method(Unsubscribe)

    # Uploads
    get_upload_url = bind_method(GetUploadUrl)
    upload_media = bind_method(UploadMedia)
