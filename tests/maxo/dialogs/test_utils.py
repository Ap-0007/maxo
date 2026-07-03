from datetime import UTC, datetime

import pytest

from maxo.dialogs.api.internal import FakeRecipient, FakeUser, RawKeyboard
from maxo.dialogs.utils import (
    add_intent_id,
    decode_reply_callback,
    encode_reply_callback,
    intent_callback_data,
    intent_payload,
    is_recipient_loaded,
    is_user_loaded,
    join_reply_callback,
    remove_intent_id,
    split_reply_callback,
    transform_to_reply_keyboard,
)
from maxo.enums import ChatType
from maxo.types import CallbackButton, MessageButton, Recipient, User


def make_user() -> User:
    return User(
        user_id=1,
        is_bot=False,
        first_name="Alice",
        last_activity_time=datetime.now(UTC),
    )


def test_reply_callback_encoding_roundtrip() -> None:
    payload = "payload"
    encoded = encode_reply_callback(payload)

    assert decode_reply_callback(encoded) == payload
    assert split_reply_callback(join_reply_callback("text", payload)) == (
        "text",
        payload,
    )
    assert split_reply_callback(None) == (None, None)


def test_transform_to_reply_keyboard() -> None:
    message_button = MessageButton(text="message")
    callback_button = CallbackButton(text="callback", payload="payload")

    keyboard = transform_to_reply_keyboard([[message_button, callback_button]])
    reply_text = keyboard[0][1].text
    assert isinstance(reply_text, str)

    assert keyboard[0][0] is message_button
    assert split_reply_callback(reply_text) == ("callback", "payload")


def test_transform_to_reply_keyboard_rejects_empty_callback_payload() -> None:
    with pytest.raises(ValueError, match="without payload"):
        transform_to_reply_keyboard([[CallbackButton(text="callback", payload="")]])


def test_intent_payload_helpers() -> None:
    payload = intent_payload("intent", "payload")

    assert payload == "intent\x1dpayload"
    assert intent_payload("intent", payload) == payload
    assert intent_payload("intent", None) is None
    assert intent_callback_data("intent", "payload") == payload
    assert remove_intent_id(payload) == ("intent", "payload")
    assert remove_intent_id("payload") == (None, "payload")


def test_add_intent_id_mutates_callback_buttons_only() -> None:
    callback = CallbackButton(text="callback", payload="payload")
    message = MessageButton(text="message")
    keyboard: RawKeyboard = [[callback, message]]

    add_intent_id(keyboard, "intent")

    assert callback.payload == "intent\x1dpayload"
    assert message.text == "message"


def test_loaded_helpers() -> None:
    recipient = Recipient(chat_id=1, user_id=1, chat_type=ChatType.DIALOG)
    fake_recipient = FakeRecipient(chat_id=1, user_id=1, chat_type=ChatType.DIALOG)
    user = make_user()
    fake_user = FakeUser(
        user_id=1,
        is_bot=False,
        first_name="Alice",
        last_activity_time=datetime.now(UTC),
    )

    assert is_recipient_loaded(recipient) is True
    assert is_recipient_loaded(fake_recipient) is False
    assert is_user_loaded(user) is True
    assert is_user_loaded(fake_user) is False
