from datetime import UTC, datetime

import pytest

from maxo.enums import ChatAdminPermission, ChatStatus, ChatType
from maxo.enums.markup_element_type import MarkupElementType
from maxo.errors import AttributeIsEmptyError
from maxo.types import (
    ChatButton,
    ContactAttachmentRequest,
    FailedUserDetails,
    MessageStat,
    ModifyMembersResult,
)
from maxo.types import BotCommand
from maxo.types import Chat
from maxo.types import ChatAdmin
from maxo.types import ChatAdminsList
from maxo.types import ChatList
from maxo.types import ChatMember
from maxo.types import ContactAttachment
from maxo.types import ContactAttachmentPayload
from maxo.types import GetPinnedMessageResult
from maxo.types import MarkupElement
from maxo.types.media_attachment_payload import MediaAttachmentPayload
from maxo.types import Message
from maxo.types.message_body import MessageBody
from maxo.types.new_message_body import NewMessageBody
from maxo.types.open_app_button import OpenAppButton
from maxo.types.photo_attachment_request import PhotoAttachmentRequest
from maxo.types.photo_attachment_request_payload import PhotoAttachmentRequestPayload
from maxo.types.photo_token import PhotoToken
from maxo.types.recipient import Recipient
from maxo.types.request_geo_location_button import RequestGeoLocationButton
from maxo.types import ShareAttachment
from maxo.types.share_attachment_payload import ShareAttachmentPayload
from maxo.types import Subscription
from maxo.types import UpdateContext
from maxo.types import UploadEndpoint
from maxo.types.uploaded_info import UploadedInfo
from maxo.types import User
from maxo.types import UserMentionMarkup
from maxo.types import UserWithPhoto
from maxo.types import VideoAttachment
from maxo.types import VideoAttachmentDetails
from maxo.types import VideoUrls

PHOTO_ID = "photo-token"
PHOTO_ATTACHMENT_ID = "photo-attachment"
SHARE_ID = "share-token"
UPLOAD_ID = "upload-token"
UPLOADED_ID = "uploaded-token"
VIDEO_ID = "video-token"
DETAILS_ID = "details-token"


def make_user() -> User:
    return User(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=datetime.now(UTC),
    )


def test_maxo_type_bot_accessors() -> None:
    user = make_user()

    with pytest.raises(AttributeIsEmptyError):
        _ = user.bot

    user.bot = None
    assert user._bot is None

    class DummyBot: ...

    bot = DummyBot()
    assert user.as_(bot) is user
    assert user.bot is bot


def test_user_and_chat_related_accessors() -> None:
    chat = Chat(
        chat_id=1,
        is_public=False,
        last_event_time=datetime.now(UTC),
        participants_count=1,
        status=ChatStatus.ACTIVE,
        type=ChatType.CHAT,
        title="Room",
    )
    chat_admin = ChatAdmin(
        user_id=1,
        permissions=[ChatAdminPermission.READ_ALL_MESSAGES],
        alias="Admin",
    )
    member = ChatMember(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=datetime.now(UTC),
        is_admin=True,
        is_owner=False,
        join_time=datetime.now(UTC),
        last_access_time=datetime.now(UTC),
        permissions=[ChatAdminPermission.READ_ALL_MESSAGES],
        alias="Admin",
        avatar_url="https://example.com/avatar.png",
        full_avatar_url="https://example.com/full.png",
    )

    assert chat_admin.unsafe_alias == "Admin"
    assert chat_admin.permissions == [ChatAdminPermission.READ_ALL_MESSAGES]
    assert member.unsafe_alias == "Admin"
    assert member.unsafe_permissions == [ChatAdminPermission.READ_ALL_MESSAGES]
    assert chat.id == 1
    assert make_user().full_name == "Alice"


def test_list_and_result_accessors() -> None:
    admin = ChatAdmin(
        user_id=1,
        permissions=[ChatAdminPermission.READ_ALL_MESSAGES],
    )
    chat = Chat(
        chat_id=1,
        is_public=False,
        last_event_time=datetime.now(UTC),
        participants_count=1,
        status=ChatStatus.ACTIVE,
        type=ChatType.CHAT,
        title="Room",
    )
    admins = ChatAdminsList(admins=[admin], marker=2)
    chats = ChatList(chats=[chat], marker=3)
    pinned_result = GetPinnedMessageResult(message=None)

    assert admins.unsafe_marker == 2
    assert chats.unsafe_marker == 3
    with pytest.raises(AttributeIsEmptyError):
        _ = pinned_result.unsafe_message


def test_markup_and_context_accessors() -> None:
    element = MarkupElement(from_=1, length=2, type=MarkupElementType.STRONG)
    mention = UserMentionMarkup(
        from_=0,
        length=5,
        type=MarkupElementType.USER_MENTION,
        user_id=10,
        user_link="@alice",
    )
    context = UpdateContext(chat_id=1, user_id=2, type=ChatType.DIALOG)

    assert element.offset == 1
    assert mention.unsafe_user_id == 10
    assert mention.unsafe_user_link == "@alice"
    assert context.chat_type == ChatType.DIALOG


def test_attachment_factories_and_unsafe_fields() -> None:
    max_info = make_user()
    contact = ContactAttachment.factory(
        max_info=max_info,
        vcf_info="BEGIN:VCARD",
    )
    photo_request = PhotoAttachmentRequest.factory(photos=["a", "b"])
    photo_payload = PhotoAttachmentRequestPayload(
        photos=[PhotoToken(token=PHOTO_ATTACHMENT_ID)],
        token=PHOTO_ID,
        url="https://example.com",
    )
    share = ShareAttachment.factory(
        url="https://example.com",
        token=SHARE_ID,
        title="Title",
        description="Desc",
        image_url="https://example.com/image.png",
    )
    subscription = Subscription(
        time=datetime.now(UTC),
        url="https://example.com",
        update_types=["message_created"],
    )
    upload = UploadEndpoint(url="https://upload.example.com", token=UPLOAD_ID)
    uploaded = UploadedInfo(token=UPLOADED_ID)
    geo = RequestGeoLocationButton(text="geo", quick=True)

    assert contact.payload.unsafe_max_info is max_info
    assert contact.payload.unsafe_vcf_info == "BEGIN:VCARD"
    assert photo_request.payload.unsafe_photos[0].token == chr(97)
    assert photo_payload.unsafe_token == PHOTO_ID
    assert share.unsafe_title == "Title"
    assert share.unsafe_description == "Desc"
    assert share.unsafe_image_url == "https://example.com/image.png"
    assert share.to_request().payload.unsafe_url == "https://example.com"
    assert subscription.unsafe_update_types == ["message_created"]
    assert upload.unsafe_token == UPLOAD_ID
    assert uploaded.unsafe_token == UPLOADED_ID
    assert geo.unsafe_quick is True
    assert contact.to_request().payload.unsafe_contact_id == 1


def test_media_and_message_models() -> None:
    message = NewMessageBody(
        attachments=[],
        format="plain",
        link=None,
        notify=True,
        text="hello",
    )
    video = VideoAttachment.factory(
        url="https://example.com/video.mp4",
        token=VIDEO_ID,
        thumbnail_url="https://example.com/thumb.png",
        width=1920,
        height=1080,
        duration=33,
    )
    details = VideoAttachmentDetails(
        duration=33,
        height=1080,
        token=DETAILS_ID,
        width=1920,
        thumbnail=ContactAttachmentPayload(vcf_info="BEGIN:VCARD"),
        urls=VideoUrls(mp4_720="https://example.com/720.mp4"),
    )
    video_urls = VideoUrls(mp4_720="https://example.com/720.mp4")

    assert message.unsafe_text == "hello"
    assert message.unsafe_notify is True
    assert video.unsafe_duration == 33
    assert video.unsafe_thumbnail.url == "https://example.com/thumb.png"
    assert video.to_request().payload.token == VIDEO_ID
    assert details.unsafe_urls.unsafe_mp4_720 == "https://example.com/720.mp4"
    assert video_urls.unsafe_mp4_720 == "https://example.com/720.mp4"


def test_remaining_optional_branches() -> None:
    message = Message(
        body=MessageBody(mid="1", seq=1, text="hello"),
        recipient=Recipient(chat_type=ChatType.DIALOG),
        timestamp=datetime.now(UTC),
        sender=make_user(),
        stat=MessageStat(views=1),
        url="https://example.com",
    )
    open_app = OpenAppButton(text="open")
    chat_button = ChatButton(
        text="create",
        type=ChatType.CHAT,
        chat_title="Room",
        chat_description="desc",
        start_payload="start",
        uuid=1,
    )
    new_message = NewMessageBody(
        attachments=[],
        format="plain",
        link=None,
        notify=True,
        text="hello",
    )
    share = ShareAttachment(
        title="Title",
        description="Desc",
        image_url="https://example.com/image.png",
    )
    modify = ModifyMembersResult(
        success=False,
        message="failed",
        failed_user_details=[FailedUserDetails(user_id=1, reason="bad")],
        failed_user_ids=[1],
    )
    photo_payload = PhotoAttachmentRequestPayload(
        photos=[PhotoToken(token="p")],
        token="t",
        url="https://example.com",
    )
    contact_request = ContactAttachmentRequest.factory(vcf_info="BEGIN:VCARD")
    subscription = Subscription(time=datetime.now(UTC), url="https://example.com")

    assert message.unsafe_sender.user_id == 1
    assert message.unsafe_stat.views == 1
    assert message.unsafe_url == "https://example.com"
    assert open_app.unsafe_contact_id is pytest.raises
    assert chat_button.unsafe_chat_description == "desc"
    assert chat_button.unsafe_start_payload == "start"
    assert chat_button.unsafe_uuid == 1
    assert new_message.unsafe_attachments == []
    assert new_message.unsafe_format == "plain"
    assert new_message.unsafe_link is None
    assert new_message.unsafe_notify is True
    assert share.unsafe_description == "Desc"
    assert share.unsafe_image_url == "https://example.com/image.png"
    assert share.unsafe_title == "Title"
    assert modify.unsafe_failed_user_details[0].user_id == 1
    assert modify.unsafe_failed_user_ids == [1]
    assert photo_payload.unsafe_photos[0].token == "p"
    assert photo_payload.unsafe_token == "t"
    assert photo_payload.unsafe_url == "https://example.com"
    assert contact_request.payload.unsafe_vcf_info == "BEGIN:VCARD"
    assert subscription.unsafe_update_types is pytest.raises


def test_additional_type_edges() -> None:
    bot_command = BotCommand(name="start")
    member = UserWithPhoto(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=datetime.now(UTC),
        username=None,
        avatar_url="https://example.com/avatar.png",
        description="About Alice",
        full_avatar_url="https://example.com/full.png",
    )

    with pytest.raises(AttributeIsEmptyError):
        _ = bot_command.unsafe_description
    assert member.unsafe_description == "About Alice"


def test_missing_optional_fields_raise_for_unsafe_accessors() -> None:
    user = make_user()
    chat_admin = ChatAdmin(user_id=1, permissions=[])
    member = UserWithPhoto(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=datetime.now(UTC),
    )
    chat_member = ChatMember(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=datetime.now(UTC),
        is_admin=False,
        is_owner=False,
        join_time=datetime.now(UTC),
        last_access_time=datetime.now(UTC),
    )
    chat_admins = ChatAdminsList(admins=[chat_admin])
    chats = ChatList(chats=[])
    pinned_result = GetPinnedMessageResult()
    geo = RequestGeoLocationButton(text="geo")
    upload = UploadEndpoint(url="https://upload.example.com")
    uploaded = UploadedInfo()
    mention = UserMentionMarkup(
        from_=0,
        length=5,
        type=MarkupElementType.USER_MENTION,
    )
    message = NewMessageBody()
    share = ShareAttachment()
    video = VideoAttachment(
        payload=MediaAttachmentPayload(url="https://example.com/video.mp4", token="v"),
    )
    details = VideoAttachmentDetails(
        duration=33,
        height=1080,
        token=DETAILS_ID,
        width=1920,
    )
    open_app = OpenAppButton(text="open")
    share_payload = ShareAttachmentPayload()
    video_urls = VideoUrls()
    message = Message(
        body=MessageBody(mid="1", seq=1, text="hello"),
        recipient=Recipient(chat_type=ChatType.DIALOG),
        timestamp=datetime.now(UTC),
    )

    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_last_name
    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_name
    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_username
    with pytest.raises(AttributeIsEmptyError):
        _ = chat_admin.unsafe_alias
    with pytest.raises(AttributeIsEmptyError):
        _ = chat_admins.unsafe_marker
    with pytest.raises(AttributeIsEmptyError):
        _ = chats.unsafe_marker
    with pytest.raises(AttributeIsEmptyError):
        _ = member.unsafe_avatar_url
    with pytest.raises(AttributeIsEmptyError):
        _ = member.unsafe_description
    with pytest.raises(AttributeIsEmptyError):
        _ = member.unsafe_full_avatar_url
    with pytest.raises(AttributeIsEmptyError):
        _ = chat_member.unsafe_alias
    with pytest.raises(AttributeIsEmptyError):
        _ = chat_member.unsafe_permissions
    with pytest.raises(AttributeIsEmptyError):
        _ = pinned_result.unsafe_message
    with pytest.raises(AttributeIsEmptyError):
        _ = geo.unsafe_quick
    with pytest.raises(AttributeIsEmptyError):
        _ = upload.unsafe_token
    with pytest.raises(AttributeIsEmptyError):
        _ = uploaded.unsafe_token
    with pytest.raises(AttributeIsEmptyError):
        _ = mention.unsafe_user_id
    with pytest.raises(AttributeIsEmptyError):
        _ = mention.unsafe_user_link
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_link
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_sender
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_stat
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_url
    with pytest.raises(AttributeIsEmptyError):
        _ = video.unsafe_duration
    with pytest.raises(AttributeIsEmptyError):
        _ = video.unsafe_height
    with pytest.raises(AttributeIsEmptyError):
        _ = video.unsafe_thumbnail
    with pytest.raises(AttributeIsEmptyError):
        _ = video.unsafe_width
    with pytest.raises(AttributeIsEmptyError):
        _ = details.unsafe_thumbnail
    with pytest.raises(AttributeIsEmptyError):
        _ = details.unsafe_urls
    with pytest.raises(AttributeIsEmptyError):
        _ = open_app.unsafe_contact_id
    with pytest.raises(AttributeIsEmptyError):
        _ = open_app.unsafe_payload
    with pytest.raises(AttributeIsEmptyError):
        _ = open_app.unsafe_web_app
    with pytest.raises(AttributeIsEmptyError):
        _ = share_payload.unsafe_token
    with pytest.raises(AttributeIsEmptyError):
        _ = share_payload.unsafe_url
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_hls
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_mp4_1080
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_mp4_144
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_mp4_240
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_mp4_360
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_mp4_480
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_mp4_720
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_link
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_sender
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_stat
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_url
