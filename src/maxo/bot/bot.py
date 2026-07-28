import asyncio
import pathlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType
from typing import BinaryIO, Self, TypeVar

from adaptix import Retort
from unihttp.bind_method import bind_method
from unihttp.clients.base import BaseAsyncClient
from unihttp.method import BaseMethod, ResponseType

from maxo import loggers
from maxo.bot.api_client import MaxApiClient, default_transport
from maxo.bot.defaults import BotDefaults
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
from maxo.bot.upload import UploadConfig
from maxo.errors import MaxBotApiError
from maxo.errors.state import StateError
from maxo.serialization import create_retort_with_bot
from maxo.types import AttachmentPayload, BotInfo, MaxoType
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import InputFile

_MethodResultT = TypeVar("_MethodResultT", bound=MaxoType)


class Bot:
    def __init__(
        self,
        token: str,
        *,
        defaults: BotDefaults | None = None,
        upload_config: UploadConfig | None = None,
        warming_up: bool = True,
        transport: BaseAsyncClient | None = None,
    ) -> None:
        self._defaults = defaults or BotDefaults()
        self._token = token
        self._warming_up = warming_up
        self._transport = transport
        self._upload_config = (
            upload_config if upload_config is not None else UploadConfig()
        )

        self._retort = create_retort_with_bot(
            bot=self,
            defaults=self._defaults,
            warming_up=warming_up,
        )

        self._api_client: MaxApiClient | None = None
        self._info: BotInfo | None = None
        self._lock = asyncio.Lock()

    @property
    def api_client(self) -> MaxApiClient:
        if self._api_client is None:
            raise StateError("Not started bot")
        return self._api_client

    @property
    def info(self) -> BotInfo:
        if self._info is None:
            raise StateError("Bot info is not resolved yet")
        return self._info

    @property
    def started(self) -> bool:
        return self._api_client is not None

    @property
    def closed(self) -> bool:
        return self._api_client is not None and self._api_client.closed

    @property
    def retort(self) -> Retort:
        return self._retort

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
    async def context(self, auto_close: bool = True) -> AsyncIterator[Self]:
        try:
            yield self
        finally:
            if auto_close:
                await self.close()

    def _build_api_client_if_needed(self) -> None:
        if self._api_client is None:
            transport = self._transport or default_transport(
                request_dumper=self._retort,
                response_loader=self._retort,
            )
            self._api_client = MaxApiClient(
                token=self._token,
                transport=transport,
                upload_config=self._upload_config,
            )

    async def start(self) -> None:
        if self._info is None:
            async with self._lock:
                if self._info is None:
                    self._build_api_client_if_needed()
                    await self.get_my_info()

    async def get_my_info(self) -> BotInfo:
        if not self.started:
            async with self._lock:
                self._build_api_client_if_needed()

        info = await self.api_client.transport.call_method(GetMyInfo())
        self._info = info
        return info

    async def close(self) -> None:
        if self._api_client is None or self._api_client.closed:
            return

        await self._api_client.close()

    async def call_method(  # for unihttp bind_method
        self,
        method: BaseMethod[ResponseType],
    ) -> ResponseType:
        await self.start()
        return await self.api_client.transport.call_method(method)

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
        await self.start()
        return await self.api_client.download(
            url=url,
            destination=destination,
            chunk_size=chunk_size,
            seek=seek,
        )

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
        await self.start()
        return await self.api_client.upload_resumable(upload_url, file, size)

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
