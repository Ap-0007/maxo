from maxo.routing.facades.base import BaseUpdateFacade
from maxo.routing.mixins import CommentMethodsFacade
from maxo.types.comment_edited import CommentEdited
from maxo.types.comment_message import CommentMessage


class CommentEditedFacade(BaseUpdateFacade[CommentEdited], CommentMethodsFacade):
    @property
    def message(self) -> CommentMessage:
        return self._update.message
