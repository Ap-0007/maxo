from maxo.types.base import MaxoType
from maxo.types.binding import BotMixin
from maxo.types.message import Message


class MessageList(MaxoType, BotMixin):
    """
    Пагинированный список сообщений

    Args:
        messages: Массив сообщений
    """

    messages: list[Message]
    """Массив сообщений"""
