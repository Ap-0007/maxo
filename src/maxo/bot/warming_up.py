from collections.abc import Iterable
from typing import Any

from adaptix import Retort
from unihttp.method import BaseMethod

from maxo.bot.binding import warm as warm_binding
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

DUMPED_ROOTS: tuple[type[BaseMethod[Any]], ...] = (
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

LOADED_ROOTS: tuple[Any, ...] = (
    Updates,
    *dict.fromkeys(method.__returning__ for method in DUMPED_ROOTS),
)


def warm_up(
    *,
    loaded: Iterable[type] | None = None,
    dumped: Iterable[type] | None = None,
    retort: Retort | None = None,
) -> None:
    from maxo.serialization import get_retort  # noqa: PLC0415 - avoids import cycle

    target = get_retort() if retort is None else retort

    loaded_roots = LOADED_ROOTS if loaded is None else loaded
    for type_ in loaded_roots:
        target.get_loader(type_)
    for type_ in DUMPED_ROOTS if dumped is None else dumped:
        target.get_dumper(type_)

    warm_binding(*loaded_roots)
