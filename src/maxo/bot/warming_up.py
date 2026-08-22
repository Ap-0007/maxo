from collections.abc import Iterable
from typing import Any

from unihttp.method import BaseMethod

from maxo.bot.methods import (
    AddMembers,
    AnswerOnCallback,
    DeleteAdmins,
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
    PostAdmins,
    RemoveMember,
    SendAction,
    SendMessage,
    SetAdmins,
    Subscribe,
    UnpinMessage,
    Unsubscribe,
    UploadMedia,
)
from maxo.types import Updates

_DUMPED_ROOTS: tuple[type[BaseMethod[Any]], ...] = (
    AddMembers,
    AnswerOnCallback,
    DeleteAdmins,
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
    PostAdmins,
    RemoveMember,
    SendAction,
    SendMessage,
    SetAdmins,
    Subscribe,
    UnpinMessage,
    Unsubscribe,
    UploadMedia,
)

_LOADED_ROOTS: tuple[Any, ...] = (
    Updates,
    *dict.fromkeys(method.__returning__ for method in _DUMPED_ROOTS),
)


def warm_up(
    *,
    loaded: Iterable[type] | None = None,
    dumped: Iterable[type] | None = None,
) -> None:
    from maxo.serialization import get_retort  # noqa: PLC0415 - avoids import cycle

    retort = get_retort()

    for type_ in _LOADED_ROOTS if loaded is None else loaded:
        retort.get_loader(type_)
    for type_ in _DUMPED_ROOTS if dumped is None else dumped:
        retort.get_dumper(type_)
