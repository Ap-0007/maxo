from maxo.routing.facades.base import BaseUpdateFacade
from maxo.routing.mixins import CommentMethodsFacade
from maxo.types.comment_created import CommentCreated
from maxo.types.comment_message import CommentMessage


class CommentCreatedFacade(BaseUpdateFacade[CommentCreated], CommentMethodsFacade):
    @property
    def message(self) -> CommentMessage:
        return self._update.message
