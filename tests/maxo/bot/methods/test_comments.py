from unihttp.bind_method import MethodBinder

from maxo import Bot
from maxo.bot.methods import (
    DeleteComment,
    EditComment,
    GetCommentById,
    GetComments,
    SendComment,
)
from maxo.serialization import create_retort
from maxo.types import (
    CommentMessage,
    CommentMessageList,
    SendCommentResult,
    SimpleQueryResult,
)


def test_wire_contracts() -> None:
    assert GetComments.__url__ == "messages/{message_id}/comments"
    assert GetComments.__method__ == "get"
    assert GetComments.__returning__ is CommentMessageList
    assert SendComment.__url__ == "messages/{message_id}/comments"
    assert SendComment.__method__ == "post"
    assert SendComment.__returning__ is SendCommentResult
    assert EditComment.__url__ == "messages/{message_id}/comments"
    assert EditComment.__method__ == "put"
    assert EditComment.__returning__ is SimpleQueryResult
    assert DeleteComment.__url__ == "messages/{message_id}/comments"
    assert DeleteComment.__method__ == "delete"
    assert DeleteComment.__returning__ is SimpleQueryResult
    assert GetCommentById.__url__ == "messages/{message_id}/comments/{comment_id}"
    assert GetCommentById.__method__ == "get"
    assert GetCommentById.__returning__ is CommentMessage


def test_bot_exposes_comment_methods() -> None:
    assert isinstance(Bot.delete_comment, MethodBinder)
    assert isinstance(Bot.edit_comment, MethodBinder)
    assert isinstance(Bot.get_comment_by_id, MethodBinder)
    assert isinstance(Bot.get_comments, MethodBinder)
    assert isinstance(Bot.send_comment, MethodBinder)


def test_dump() -> None:
    retort = create_retort(warming_up=False)

    assert retort.dump(GetComments(message_id="post")) == {
        "path": {"message_id": "post"},
        "query": {},
    }
    assert retort.dump(SendComment(message_id="post", text="Текст")) == {
        "path": {"message_id": "post"},
        "query": {},
        "body": {"link": None, "text": "Текст"},
    }
    assert retort.dump(EditComment(message_id="post", comment_id="comment")) == {
        "path": {"message_id": "post"},
        "query": {"comment_id": "comment"},
        "body": {"link": None, "text": None},
    }
    assert retort.dump(DeleteComment(message_id="post", comment_id="comment")) == {
        "path": {"message_id": "post"},
        "query": {"comment_id": "comment"},
    }
    assert retort.dump(GetCommentById(message_id="post", comment_id="comment")) == {
        "path": {"message_id": "post", "comment_id": "comment"},
    }


def test_comment_message_loads_null_sender() -> None:
    retort = create_retort(warming_up=False)
    raw = {
        "sender": None,
        "recipient": {
            "chat_type": "channel",
            "chat_id": 10,
            "user_id": None,
            "post_id": "post",
        },
        "timestamp": 0,
        "body": {
            "mid": "comment",
            "seq": 1,
            "text": "Текст",
        },
    }

    comment = retort.load(raw, CommentMessage)

    assert comment.sender is None
