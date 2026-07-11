# ruff: noqa: E402

import warnings

warnings.warn(
    "Апдейты были перенесены из `maxo.routing.updates` в `maxo.types`. "
    "Пожалуйста, обновите импорты "
    "на `from maxo.types import ...` ",
    DeprecationWarning,
    stacklevel=2,
)

from maxo.types.base import BaseUpdate, MaxUpdate
from maxo.types.bot_added_to_chat import BotAddedToChat
from maxo.types.bot_removed_from_chat import BotRemovedFromChat
from maxo.types.bot_started import BotStarted
from maxo.types.bot_stopped import BotStopped
from maxo.types.chat_title_changed import ChatTitleChanged
from maxo.types.dialog_cleared import DialogCleared
from maxo.types.dialog_muted import DialogMuted
from maxo.types.dialog_removed import DialogRemoved
from maxo.types.dialog_unmuted import DialogUnmuted
from maxo.types.error_event import ErrorEvent
from maxo.types.message_callback import CallbackQuery, MessageCallback
from maxo.types.message_created import MessageCreated
from maxo.types.message_edited import MessageEdited
from maxo.types.message_removed import MessageRemoved
from maxo.types.updates import Updates
from maxo.types.user_added_to_chat import UserAddedToChat
from maxo.types.user_removed_from_chat import UserRemovedFromChat

__all__ = (
    "BaseUpdate",
    "BotAddedToChat",
    "BotRemovedFromChat",
    "BotStarted",
    "BotStopped",
    "CallbackQuery",
    "ChatTitleChanged",
    "DialogCleared",
    "DialogMuted",
    "DialogRemoved",
    "DialogUnmuted",
    "ErrorEvent",
    "MaxUpdate",
    "MessageCallback",
    "MessageCreated",
    "MessageEdited",
    "MessageRemoved",
    "Updates",
    "UserAddedToChat",
    "UserRemovedFromChat",
)
