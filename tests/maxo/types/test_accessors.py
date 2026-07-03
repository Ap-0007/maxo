from datetime import UTC, datetime

import pytest

from maxo.enums import AttachmentType, ChatAdminPermission, ChatStatus, ChatType
from maxo.enums.message_link_type import MessageLinkType
from maxo.enums.text_format import TextFormat
from maxo.errors import AttributeIsEmptyError
from maxo.types import (
    AudioAttachment,
    BotCommand,
    BotInfo,
    Callback,
    CallbackButton,
    Chat,
    ChatAdmin,
    ChatMember,
    ContactAttachment,
    ContactAttachmentPayload,
    ContactAttachmentRequestPayload,
    FileAttachment,
    GetPinnedMessageResult,
    Image,
    InlineKeyboardAttachment,
    Keyboard,
    LinkedMessage,
    LocationAttachment,
    Message,
    MessageBody,
    MessageButton,
    MessageStat,
    ModifyMembersResult,
    NewMessageBody,
    NewMessageLink,
    OpenAppButton,
    PhotoAttachment,
    PhotoAttachmentRequestPayload,
    PhotoToken,
    Recipient,
    RequestGeoLocationButton,
    ShareAttachment,
    ShareAttachmentPayload,
    SimpleQueryResult,
    StickerAttachment,
    Subscription,
    UploadEndpoint,
    UploadMediaResult,
    User,
    UserMentionMarkup,
    UserWithPhoto,
    VideoAttachment,
    VideoAttachmentDetails,
    VideoThumbnail,
    VideoUrls,
)
from maxo.types.uploaded_info import UploadedInfo

TOKEN = "attachment-token"  # noqa: S105


def make_user() -> User:
    return User(
        user_id=1,
        first_name="Alice",
        last_name="Tester",
        name="Alice T.",
        username="alice",
        is_bot=False,
        last_activity_time=datetime.now(UTC),
    )


def make_chat(**kwargs: object) -> Chat:
    data = {
        "chat_id": 10,
        "is_public": True,
        "last_event_time": datetime.now(UTC),
        "participants_count": 2,
        "status": ChatStatus.ACTIVE,
        "type": ChatType.CHAT,
    }
    data.update(kwargs)
    return Chat(**data)  # type: ignore[arg-type]


def make_message(**kwargs: object) -> Message:
    data = {
        "body": MessageBody(mid="mid", seq=7, text="hello"),
        "recipient": Recipient(chat_type=ChatType.CHAT, chat_id=10),
        "timestamp": datetime.now(UTC),
    }
    data.update(kwargs)
    return Message(**data)  # type: ignore[arg-type]


def test_user_accessors() -> None:
    user = make_user()

    assert user.id == 1
    assert user.fullname == "Alice Tester"
    assert user.full_name == "Alice Tester"
    assert user.unsafe_last_name == "Tester"
    assert user.unsafe_name == "Alice T."
    assert user.unsafe_username == "alice"


def test_user_unsafe_accessors_raise_for_omitted_fields() -> None:
    user = User(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=datetime.now(UTC),
    )

    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_last_name
    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_name
    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_username


def test_bot_info_commands_accessor() -> None:
    commands = [BotCommand(name="start", description="Start")]
    info = BotInfo(
        user_id=1,
        first_name="Bot",
        username="bot",
        is_bot=True,
        last_activity_time=datetime.now(UTC),
        commands=commands,
    )

    assert info.unsafe_commands is commands


def test_bot_info_commands_accessor_raises_for_omitted_value() -> None:
    info = BotInfo(
        user_id=1,
        first_name="Bot",
        username="bot",
        is_bot=True,
        last_activity_time=datetime.now(UTC),
    )

    with pytest.raises(AttributeIsEmptyError):
        _ = info.unsafe_commands


def test_chat_accessors_for_defined_values() -> None:
    icon = Image(url="https://example.com/icon.png")
    user = make_user()
    message = make_message()
    participants = {"1": {"last_activity_time": 1}}
    chat = make_chat(
        chat_message_id="button-message",
        description="chat",
        dialog_with_user=user,
        icon=icon,
        link="https://max.ru/join",
        messages_count=3,
        owner_id=1,
        participants=participants,
        pinned_message=message,
        title="Chat",
    )

    assert chat.id == 10
    assert chat.unsafe_chat_message_id == "button-message"
    assert chat.unsafe_description == "chat"
    assert chat.unsafe_dialog_with_user is user
    assert chat.unsafe_icon is icon
    assert chat.unsafe_link == "https://max.ru/join"
    assert chat.unsafe_messages_count == 3
    assert chat.unsafe_owner_id == 1
    assert chat.unsafe_participants is participants
    assert chat.unsafe_pinned_message is message
    assert chat.unsafe_title == "Chat"


def test_chat_accessors_raise_for_explicit_none_values() -> None:
    chat = make_chat(description=None, icon=None, title=None)

    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_description
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_icon
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_title


def test_chat_accessors_raise_for_omitted_values() -> None:
    chat = make_chat()

    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_chat_message_id
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_dialog_with_user
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_link
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_messages_count
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_owner_id
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_participants
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_pinned_message


def test_message_accessors_and_generated_url() -> None:
    stat = MessageStat(views=5)
    sender = make_user()
    message = make_message(sender=sender, stat=stat, url="https://max.ru/post")

    assert message.message is message
    assert message.unsafe_sender is sender
    assert message.unsafe_stat is stat
    assert message.unsafe_url == "https://max.ru/post"
    assert message.generated_url is not None
    assert message.unsafe_generated_url == message.generated_url


def test_message_generated_url_is_none_without_chat_id() -> None:
    message = make_message(
        recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
    )

    assert message.generated_url is None
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_generated_url


def test_recipient_accessors() -> None:
    recipient = Recipient(chat_type=ChatType.CHAT, chat_id=10, user_id=1)

    assert recipient.unsafe_chat_id == 10
    assert recipient.unsafe_user_id == 1


def test_recipient_accessors_raise_for_missing_values() -> None:
    recipient = Recipient(chat_type=ChatType.CHAT)

    with pytest.raises(AttributeIsEmptyError):
        _ = recipient.unsafe_chat_id
    with pytest.raises(AttributeIsEmptyError):
        _ = recipient.unsafe_user_id


def test_message_body_attachment_accessors() -> None:
    keyboard = Keyboard(buttons=[])
    photo = PhotoAttachment.factory(photo_id=1, token=TOKEN, url="photo-url")
    video = VideoAttachment.factory(url="video-url", token=TOKEN)
    audio = AudioAttachment.factory(url="audio-url", token=TOKEN)
    file = FileAttachment.factory(
        url="file-url",
        token=TOKEN,
        filename="file.txt",
        size=10,
    )
    sticker = StickerAttachment.factory(
        url="sticker-url",
        code="sticker-code",
        width=10,
        height=10,
    )
    contact = ContactAttachment.factory(max_info=make_user())
    share = ShareAttachment.factory(url="https://example.com")
    location = LocationAttachment(latitude=1.0, longitude=2.0)
    body = MessageBody(
        mid="mid",
        seq=1,
        text="text",
        attachments=[
            InlineKeyboardAttachment(payload=keyboard),
            photo,
            video,
            audio,
            file,
            sticker,
            contact,
            share,
            location,
        ],
        markup=[],
    )

    assert body.id == "mid"
    assert body.keyboard is keyboard
    assert body.reply_markup is keyboard
    assert body.photo == [photo]
    assert body.video == [video]
    assert body.audio is audio
    assert body.file is file
    assert body.sticker is sticker
    assert body.contact is contact
    assert body.share is share
    assert body.location is location
    assert body.unsafe_attachments == body.attachments
    assert body.unsafe_markup == []
    assert body.unsafe_text == "text"
    assert body.html_text == "text"
    assert body.md_text == "text"


@pytest.mark.parametrize(
    ("body", "attachment_type"),
    [
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[
                    PhotoAttachment.factory(
                        photo_id=1,
                        token=TOKEN,
                        url="photo-url",
                    ),
                ],
            ),
            AttachmentType.PHOTO,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[VideoAttachment.factory(url="url", token=TOKEN)],
            ),
            AttachmentType.VIDEO,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[AudioAttachment.factory(url="url", token=TOKEN)],
            ),
            AttachmentType.AUDIO,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[
                    FileAttachment.factory(
                        url="url",
                        token=TOKEN,
                        filename="file",
                        size=1,
                    ),
                ],
            ),
            AttachmentType.FILE,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[
                    StickerAttachment.factory(
                        url="url",
                        code="code",
                        width=1,
                        height=1,
                    ),
                ],
            ),
            AttachmentType.STICKER,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[ContactAttachment.factory(max_info=make_user())],
            ),
            AttachmentType.CONTACT,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[ShareAttachment.factory(url="https://example.com")],
            ),
            AttachmentType.SHARE,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[LocationAttachment(latitude=1.0, longitude=2.0)],
            ),
            AttachmentType.LOCATION,
        ),
        (MessageBody(mid="mid", seq=1, text="text"), AttachmentType.TEXT),
        (MessageBody(mid="mid", seq=1), AttachmentType.UNKNOWN),
    ],
)
def test_message_body_attachment_type(
    body: MessageBody,
    attachment_type: AttachmentType,
) -> None:
    assert body.attachment_type is attachment_type
    assert body.content_type is attachment_type


def test_message_body_unsafe_accessors_raise_for_omitted_values() -> None:
    body = MessageBody(mid="mid", seq=1)

    with pytest.raises(AttributeIsEmptyError):
        _ = body.unsafe_markup
    with pytest.raises(AttributeIsEmptyError):
        _ = body.unsafe_text


def test_message_body_unsafe_attachments_raises_for_explicit_none() -> None:
    body = MessageBody(mid="mid", seq=1, attachments=None)

    with pytest.raises(AttributeIsEmptyError):
        _ = body.unsafe_attachments


def test_callback_accessors() -> None:
    callback = Callback(
        callback_id="callback",
        timestamp=datetime.now(UTC),
        user=make_user(),
        payload="payload",
    )

    assert callback.id == "callback"
    assert callback.data == "payload"
    assert callback.unsafe_payload == "payload"
    assert callback.unsafe_data == "payload"

    with pytest.raises(AttributeIsEmptyError):
        _ = Callback(
            callback_id="callback",
            timestamp=datetime.now(UTC),
            user=make_user(),
        ).unsafe_payload


def test_linked_message_accessors_and_generated_url() -> None:
    sender = make_user()
    linked = LinkedMessage(
        type=MessageLinkType.FORWARD,
        message=MessageBody(mid="mid", seq=5, text="forwarded"),
        chat_id=10,
        sender=sender,
    )

    assert linked.unsafe_chat_id == 10
    assert linked.unsafe_sender is sender
    assert linked.generated_url is not None
    assert linked.unsafe_generated_url == linked.generated_url

    omitted = LinkedMessage(
        type=MessageLinkType.REPLY,
        message=MessageBody(mid="mid", seq=5, text="reply"),
    )
    assert omitted.generated_url is None
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_chat_id
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_sender
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_generated_url


def test_new_message_body_accessors() -> None:
    link = NewMessageLink(mid="mid", type=MessageLinkType.REPLY)
    body = NewMessageBody(
        attachments=[],
        format=TextFormat.MARKDOWN,
        link=link,
        notify=False,
        text="text",
    )

    assert body.unsafe_attachments == []
    assert body.unsafe_format is TextFormat.MARKDOWN
    assert body.unsafe_link is link
    assert body.unsafe_notify is False
    assert body.unsafe_text == "text"

    omitted = NewMessageBody()
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_format
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_notify


def test_media_attachment_to_request_factories() -> None:
    assert AudioAttachment.factory(url="url", token=TOKEN).to_request().payload.token
    assert (
        FileAttachment.factory(
            url="url",
            token=TOKEN,
            filename="file",
            size=1,
        )
        .to_request()
        .payload.token
        == TOKEN
    )
    assert (
        PhotoAttachment.factory(
            photo_id=1,
            token=TOKEN,
            url="url",
        )
        .to_request()
        .payload.token
        == TOKEN
    )
    assert (
        StickerAttachment.factory(
            url="url",
            code="code",
            width=1,
            height=1,
        )
        .to_request()
        .payload.code
        == "code"
    )
    assert (
        VideoAttachment.factory(
            url="url",
            token=TOKEN,
            thumbnail_url="thumbnail",
            width=1,
            height=2,
            duration=3,
        )
        .to_request()
        .payload.token
        == TOKEN
    )
    assert InlineKeyboardAttachment.factory([]).to_request().payload.buttons == []
    assert LocationAttachment(latitude=1.0, longitude=2.0).to_request().latitude == 1.0


def test_media_attachment_unsafe_optional_values() -> None:
    audio = AudioAttachment.factory(url="url", token=TOKEN, transcription="text")
    video = VideoAttachment.factory(
        url="url",
        token=TOKEN,
        thumbnail_url="thumbnail",
        width=1,
        height=2,
        duration=3,
    )
    share = ShareAttachment.factory(
        url="url",
        token=TOKEN,
        title="title",
        description="description",
        image_url="image",
    )

    assert audio.unsafe_transcription == "text"
    assert video.unsafe_width == 1
    assert video.unsafe_height == 2
    assert video.unsafe_duration == 3
    assert isinstance(video.unsafe_thumbnail, VideoThumbnail)
    assert share.unsafe_title == "title"
    assert share.unsafe_description == "description"
    assert share.unsafe_image_url == "image"
    assert share.to_request().payload.token == TOKEN

    with pytest.raises(AttributeIsEmptyError):
        _ = AudioAttachment.factory(url="url", token=TOKEN).unsafe_transcription
    with pytest.raises(AttributeIsEmptyError):
        _ = VideoAttachment.factory(url="url", token=TOKEN).unsafe_width
    with pytest.raises(AttributeIsEmptyError):
        _ = ShareAttachment().unsafe_title


def test_contact_attachment_request_payload_accessors() -> None:
    payload = ContactAttachmentRequestPayload(
        contact_id=1,
        name="Alice",
        vcf_info="BEGIN:VCARD",
        vcf_phone="+1",
    )

    assert payload.unsafe_contact_id == 1
    assert payload.unsafe_name == "Alice"
    assert payload.unsafe_vcf_info == "BEGIN:VCARD"
    assert payload.unsafe_vcf_phone == "+1"

    omitted = ContactAttachmentRequestPayload()
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_contact_id
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_vcf_info


def test_contact_attachment_payload_accessors() -> None:
    user = make_user()
    payload = ContactAttachmentPayload(
        hash="hash",
        max_info=user,
        vcf_info="BEGIN:VCARD",
    )

    assert payload.unsafe_hash == "hash"
    assert payload.unsafe_max_info is user
    assert payload.unsafe_vcf_info == "BEGIN:VCARD"

    omitted = ContactAttachmentPayload()
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_hash
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_max_info


def test_photo_request_payload_and_share_payload_accessors() -> None:
    photo_token = PhotoToken(token=TOKEN)
    photo_payload = PhotoAttachmentRequestPayload(
        photos=[photo_token],
        token=TOKEN,
        url="url",
    )
    share_payload = ShareAttachmentPayload(token=TOKEN, url="url")

    assert photo_payload.unsafe_photos == [photo_token]
    assert photo_payload.unsafe_token == TOKEN
    assert photo_payload.unsafe_url == "url"
    assert share_payload.unsafe_token == TOKEN
    assert share_payload.unsafe_url == "url"

    with pytest.raises(AttributeIsEmptyError):
        _ = PhotoAttachmentRequestPayload().unsafe_token
    with pytest.raises(AttributeIsEmptyError):
        _ = ShareAttachmentPayload().unsafe_url


def test_video_urls_and_details_accessors() -> None:
    urls = VideoUrls(
        hls="hls",
        mp4_1080="1080",
        mp4_144="144",
        mp4_240="240",
        mp4_360="360",
        mp4_480="480",
        mp4_720="720",
    )
    details = VideoAttachmentDetails(
        duration=1,
        height=2,
        token=TOKEN,
        width=3,
        thumbnail=PhotoAttachment.factory(
            photo_id=1,
            token=TOKEN,
            url="thumbnail",
        ).payload,
        urls=urls,
    )

    assert urls.unsafe_hls == "hls"
    assert urls.unsafe_mp4_1080 == "1080"
    assert urls.unsafe_mp4_144 == "144"
    assert urls.unsafe_mp4_240 == "240"
    assert urls.unsafe_mp4_360 == "360"
    assert urls.unsafe_mp4_480 == "480"
    assert urls.unsafe_mp4_720 == "720"
    assert details.unsafe_thumbnail.url == "thumbnail"
    assert details.unsafe_urls is urls

    with pytest.raises(AttributeIsEmptyError):
        _ = VideoUrls().unsafe_hls
    with pytest.raises(AttributeIsEmptyError):
        _ = VideoAttachmentDetails(
            duration=1,
            height=2,
            token=TOKEN,
            width=3,
        ).unsafe_urls


def test_small_generated_accessors() -> None:
    permissions = [ChatAdminPermission.READ_ALL_MESSAGES]
    failed_users = [1, 2]

    assert BotCommand(name="start", description="desc").unsafe_description == "desc"
    assert CallbackButton(text="callback", payload="payload").callback_data == "payload"
    assert ChatAdmin(user_id=1, permissions=permissions, alias="admin").unsafe_alias
    assert (
        ChatMember(
            user_id=1,
            first_name="Alice",
            is_bot=False,
            last_activity_time=datetime.now(UTC),
            join_time=datetime.now(UTC),
            last_access_time=datetime.now(UTC),
            is_admin=True,
            is_owner=False,
            alias="admin",
            permissions=permissions,
        ).unsafe_permissions
        == permissions
    )
    assert (
        GetPinnedMessageResult(message=make_message()).unsafe_message.message
        is not None
    )
    assert MessageButton(text="text").unsafe_text == "text"
    assert (
        ModifyMembersResult(
            success=True,
            failed_user_ids=failed_users,
        ).unsafe_failed_user_ids
        == failed_users
    )
    assert OpenAppButton(
        text="open",
        contact_id=1,
        payload="payload",
        web_app="app",
    ).unsafe_payload
    assert RequestGeoLocationButton(text="geo", quick=True).unsafe_quick is True
    assert SimpleQueryResult(success=True, message="ok").unsafe_message == "ok"
    assert Subscription(
        time=datetime.now(UTC),
        url="https://example.com/webhook",
        update_types=["message_created"],
    ).unsafe_update_types == ["message_created"]
    assert UploadEndpoint(url="url", token=TOKEN).unsafe_token == TOKEN
    assert UploadedInfo(token=TOKEN).unsafe_token == TOKEN
    assert (
        UserMentionMarkup(
            from_=0,
            length=4,
            user_id=1,
            user_link="https://max.ru/u",
        ).unsafe_user_id
        == 1
    )
    assert (
        UserWithPhoto(
            user_id=1,
            first_name="Alice",
            is_bot=False,
            last_activity_time=datetime.now(UTC),
            avatar_url="avatar",
            description="description",
            full_avatar_url="full",
        ).unsafe_full_avatar_url
        == "full"
    )


def test_upload_media_result_last_token() -> None:
    photo_token = "photo-upload-token"  # noqa: S105

    assert UploadMediaResult(token=TOKEN).last_token == TOKEN
    assert (
        UploadMediaResult(photos={"1": PhotoToken(token=photo_token)}).last_token
        == photo_token
    )

    with pytest.raises(RuntimeError):
        _ = UploadMediaResult().last_token
