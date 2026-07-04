from datetime import UTC, datetime
from typing import cast

from maxo.dialogs.test_tools.keyboard import (
    InlineButtonDataLocator,
    InlineButtonPositionLocator,
    InlineButtonTextLocator,
)
from maxo.enums import ChatType
from maxo.types import (
    Attachments,
    CallbackButton,
    InlineButtons,
    InlineKeyboardAttachment,
    LinkButton,
    Message,
    MessageBody,
    Recipient,
)


def make_message(buttons: list[list[InlineButtons]] | None) -> Message:
    attachments: list[Attachments] | None = None
    if buttons is not None:
        attachments = [InlineKeyboardAttachment.factory(buttons=buttons)]
    return Message(
        body=MessageBody(mid="mid", seq=1, attachments=attachments),
        recipient=Recipient(chat_type=ChatType.CHAT, chat_id=42),
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_text_locator_finds_button_by_full_match() -> None:
    button = CallbackButton(text="Open", payload="payload")
    message = make_message(
        [[LinkButton(text="Docs", url="https://example.com"), button]],
    )

    assert InlineButtonTextLocator("Op.n").find_button(message) is button
    assert InlineButtonTextLocator("pen").find_button(message) is None


def test_text_locator_ignores_buttons_without_text() -> None:
    # MAX inline buttons currently have text, this guards the defensive branch.
    button = cast(InlineButtons, object())
    message = make_message([[button]])

    assert InlineButtonTextLocator(".*").find_button(message) is None


def test_locators_return_none_without_keyboard() -> None:
    message = make_message(None)

    assert InlineButtonTextLocator(".*").find_button(message) is None
    assert InlineButtonPositionLocator(0, 0).find_button(message) is None
    assert InlineButtonDataLocator(".*").find_button(message) is None


def test_position_locator_returns_button_or_none_for_missing_position() -> None:
    button = CallbackButton(text="Open", payload="payload")
    message = make_message([[button]])

    assert InlineButtonPositionLocator(0, 0).find_button(message) is button
    assert InlineButtonPositionLocator(1, 0).find_button(message) is None
    assert InlineButtonPositionLocator(0, 1).find_button(message) is None


def test_data_locator_finds_callback_button_only() -> None:
    button = CallbackButton(text="Open", payload="payload-42")
    message = make_message([[LinkButton(text="Docs", url="payload-42"), button]])

    assert InlineButtonDataLocator("payload-\\d+").find_button(message) is button
    assert InlineButtonDataLocator("missing").find_button(message) is None


def test_locator_repr() -> None:
    assert repr(InlineButtonTextLocator("Open")) == "InlineButtonTextLocator('Open')"
    assert repr(InlineButtonPositionLocator(1, 2)) == (
        "InlineButtonPositionLocator(row=1, column=2)"
    )
    assert repr(InlineButtonDataLocator("payload")) == (
        "InlineButtonDataLocator('payload')"
    )
