from datetime import UTC, datetime

import pytest

from maxo.enums import ButtonType, ChatType
from maxo.errors import AttributeIsEmptyError
from maxo.types import (
    ChatButton,
    Message,
    MessageBody,
    MessageButton,
    OpenAppButton,
    Recipient,
    SimpleQueryResult,
    UpdateList,
    UserWithPhoto,
    VideoUrls,
)


def test_base_message_button_and_chat_button_accessors() -> None:
    message_button = MessageButton(text="Hello")
    chat_button = ChatButton(
        text="Create chat",
        type=ButtonType.MESSAGE,
        chat_title="Chat",
        chat_description="Desc",
    )

    assert message_button.unsafe_text == "Hello"
    assert chat_button.unsafe_chat_description == "Desc"


def test_button_accessors_raise_for_omitted_values() -> None:
    message_button = MessageButton()
    chat_button = ChatButton(text="Create chat", type=ButtonType.MESSAGE, chat_title="Chat")
    open_app_button = OpenAppButton(text="Open")

    with pytest.raises(AttributeIsEmptyError):
        _ = message_button.unsafe_text
    with pytest.raises(AttributeIsEmptyError):
        _ = chat_button.unsafe_chat_description
    with pytest.raises(AttributeIsEmptyError):
        _ = chat_button.unsafe_start_payload
    with pytest.raises(AttributeIsEmptyError):
        _ = chat_button.unsafe_uuid
    with pytest.raises(AttributeIsEmptyError):
        _ = open_app_button.unsafe_contact_id
    with pytest.raises(AttributeIsEmptyError):
        _ = open_app_button.unsafe_payload
    with pytest.raises(AttributeIsEmptyError):
        _ = open_app_button.unsafe_web_app


def test_video_urls_and_user_with_photo_accessors() -> None:
    urls = VideoUrls(
        hls="https://example.com/hls.m3u8",
        mp4_1080="https://example.com/1080.mp4",
    )
    user = UserWithPhoto(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=datetime.now(UTC),
        avatar_url="https://example.com/avatar.png",
        description="About Alice",
        full_avatar_url="https://example.com/full.png",
    )

    assert urls.unsafe_hls == "https://example.com/hls.m3u8"
    assert urls.unsafe_mp4_1080 == "https://example.com/1080.mp4"
    assert user.unsafe_avatar_url == "https://example.com/avatar.png"
    assert user.unsafe_description == "About Alice"
    assert user.unsafe_full_avatar_url == "https://example.com/full.png"


def test_update_list_and_simple_query_result_accessors() -> None:
    update_list = UpdateList(updates=[], marker=10)
    query_result = SimpleQueryResult(success=True, message="ok")

    assert update_list.unsafe_marker == 10
    assert query_result.unsafe_message == "ok"


def test_update_list_and_simple_query_result_raise_for_missing_values() -> None:
    update_list = UpdateList(updates=[])
    query_result = SimpleQueryResult(success=False)

    with pytest.raises(AttributeIsEmptyError):
        _ = update_list.unsafe_marker
    with pytest.raises(AttributeIsEmptyError):
        _ = query_result.unsafe_message


def test_message_generated_url_requires_chat_id() -> None:
    message = Message(
        body=MessageBody(mid="1", seq=1, text="hello"),
        recipient=Recipient(chat_type=ChatType.DIALOG),
        timestamp=datetime.now(UTC),
    )

    assert message.generated_url is None
