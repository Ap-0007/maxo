from abc import abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

from maxo.enums import TextFormat
from maxo.omit import Omittable, Omitted, is_defined
from maxo.routing.mixins.attachments import MediaInput
from maxo.routing.mixins.message import MessageMethodsFacade
from maxo.types.attachments import AttachmentsRequests
from maxo.types.buttons import InlineButtons
from maxo.types.new_message_link import NewMessageLink
from maxo.types.simple_query_result import SimpleQueryResult

if TYPE_CHECKING:
    from maxo.types.comment_message import CommentMessage


class CommentMethodsFacade(MessageMethodsFacade):
    __slots__ = ()

    if TYPE_CHECKING:

        @property
        @abstractmethod
        def message(self) -> "CommentMessage | None":
            raise NotImplementedError

    else:
        message: "CommentMessage | None"

    async def delete_message(self) -> SimpleQueryResult:
        comment = self.unsafe_message
        return await self.bot.delete_comment(
            message_id=comment.recipient.unsafe_post_id,
            comment_id=comment.body.mid,
        )

    async def send_message(
        self,
        text: str | None = None,
        link: NewMessageLink | None = None,
        notify: Omittable[bool] = True,
        format: Omittable[TextFormat | None] = Omitted(),
        disable_link_preview: Omittable[bool] = Omitted(),
        keyboard: Sequence[Sequence[InlineButtons]] | None = None,
        media: Sequence[MediaInput] | None = None,
        attachments: Sequence[AttachmentsRequests] | None = None,
    ) -> "CommentMessage":
        if (
            keyboard is not None
            or media is not None
            or attachments is not None
            or (is_defined(notify) and not notify)
        ):
            raise ValueError("Комментарии не поддерживают вложения и notify=False")

        result = await self.bot.send_comment(
            message_id=self.unsafe_message.recipient.unsafe_post_id,
            text=text,
            link=link,
            format=format,
            disable_link_preview=disable_link_preview,
        )
        return result.message

    # Алиас сужает результат Message до CommentMessage
    answer = send_message  # type: ignore[mutable-override]

    async def edit_message(
        self,
        text: str | None = None,
        keyboard: Sequence[Sequence[InlineButtons]] | None = None,
        media: Sequence[MediaInput] | None = None,
        link: NewMessageLink | None = None,
        notify: bool = True,
        format: Omittable[TextFormat | None] = Omitted(),
        attachments: Sequence[AttachmentsRequests] | None = None,
    ) -> SimpleQueryResult:
        comment = self.unsafe_message
        if (
            keyboard is not None
            or media is not None
            or attachments is not None
            or not notify
        ):
            raise ValueError("Комментарии не поддерживают вложения и notify=False")

        if text is None:
            text = comment.body.text

        return await self.bot.edit_comment(
            message_id=comment.recipient.unsafe_post_id,
            comment_id=comment.body.mid,
            text=text,
            link=link,
            format=format,
        )

    async def get_message_by_id(self, message_id: str) -> "CommentMessage":
        return await self.bot.get_comment_by_id(
            message_id=self.unsafe_message.recipient.unsafe_post_id,
            comment_id=message_id,
        )
