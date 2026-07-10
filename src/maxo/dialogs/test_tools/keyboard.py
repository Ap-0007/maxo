import re
from typing import Protocol

from maxo.omit import is_defined
from maxo.types import CallbackButton, InlineButtons, Message


class InlineButtonLocator(Protocol):
    def find_button(
        self,
        message: Message,
    ) -> InlineButtons | None:
        raise NotImplementedError


class InlineButtonTextLocator:
    def __init__(self, regex: str) -> None:
        self.regex = re.compile(regex)

    def find_button(
        self,
        message: Message,
    ) -> InlineButtons | None:
        if not message.body.keyboard:
            return None
        for row in message.body.keyboard.buttons:
            for button in row:
                text = getattr(button, "text", None)
                if text is None or not is_defined(text):
                    continue
                if self.regex.fullmatch(text):
                    return button
        return None

    def __repr__(self) -> str:
        return f"InlineButtonTextLocator({self.regex.pattern!r})"


class InlineButtonPositionLocator:
    def __init__(self, row: int, column: int) -> None:
        self.row = row
        self.column = column

    def find_button(
        self,
        message: Message,
    ) -> InlineButtons | None:
        if not message.body.keyboard:
            return None
        try:
            return message.body.keyboard.buttons[self.row][self.column]
        except IndexError:
            return None

    def __repr__(self) -> str:
        return f"InlineButtonPositionLocator(row={self.row}, column={self.column})"


class InlineButtonDataLocator:
    def __init__(self, regex: str) -> None:
        self.regex = re.compile(regex)

    def find_button(
        self,
        message: Message,
    ) -> InlineButtons | None:
        if not message.body.keyboard:
            return None
        for row in message.body.keyboard.buttons:
            for button in row:
                if not isinstance(button, CallbackButton):
                    continue
                if self.regex.fullmatch(button.payload):
                    return button
        return None

    def __repr__(self) -> str:
        return f"InlineButtonDataLocator({self.regex.pattern!r})"
