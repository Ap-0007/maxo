from enum import StrEnum


class ChatType(StrEnum):
    """Тип чата: диалог, чат"""

    CHANNEL = "channel"
    CHAT = "chat"
    DIALOG = "dialog"

    # Подражание aiogram
    PRIVATE = DIALOG
    GROUP = CHAT
    SUPERGROUP = CHAT
