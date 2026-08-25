from maxo.enums.update_type import UpdateType
from maxo.routing.mixins import CommentMethodsFacade
from maxo.types.base import MaxUpdate
from maxo.types.comment_message import CommentMessage


class CommentEdited(MaxUpdate, CommentMethodsFacade):
    """
    Вы получите это событие, как только пользователь отредактирует комментарий

    Args:
        message: Отредактированный комментарий
        type:
    """

    type = UpdateType.COMMENT_EDITED

    message: CommentMessage
    """Отредактированный комментарий"""
