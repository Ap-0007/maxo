"""Точечные тесты на редко используемые ветки утилит."""

import pytest

from maxo.types import CallbackButton
from maxo.types.buttons import InlineButtons
from maxo.utils.builders.keyboard import (
    KeyboardBuilder,
    KeyboardValidator,
    repeat_last,
)
from maxo.utils.formatting import Text, as_line, as_list


class TestFormattingHelpers:
    def test_as_line_without_items(self) -> None:
        assert as_line().render()[0] == "\n"

    def test_as_line_with_separator(self) -> None:
        text, _ = as_line("a", "b", sep="-").render()

        assert text == "a-b\n"

    def test_as_line_without_separator(self) -> None:
        text, _ = as_line("a", "b").render()

        assert text == "ab\n"

    def test_as_list_without_items(self) -> None:
        assert as_list().render()[0] == ""

    def test_as_kwargs_replaces_format(self) -> None:
        kwargs = Text("hello").as_kwargs(replace_format=True)

        assert kwargs["text"] == "hello"
        assert kwargs["format"] is None

    def test_as_kwargs_without_replace_keeps_format_key_absent(self) -> None:
        assert Text("hello").as_kwargs(replace_format=False) == {"text": "hello"}

    def test_node_without_type_cannot_be_entity(self) -> None:
        with pytest.raises(ValueError, match="Node without type"):
            Text("x")._render_entity(offset=0, length=1)


class TestRepeatLast:
    def test_empty_iterable(self) -> None:
        assert list(repeat_last([])) == []

    def test_repeats_last_value(self) -> None:
        generator = repeat_last([1, 2])

        assert [next(generator) for _ in range(4)] == [1, 2, 2, 2]


class TestKeyboardValidator:
    def test_too_many_buttons(self) -> None:
        validator = KeyboardValidator()
        buttons: list[list[InlineButtons]] = [
            [CallbackButton(text=str(i), payload=str(i))]
            for i in range(validator.max_buttons + 1)
        ]

        with pytest.raises(ValueError, match="Too much buttons"):
            validator.validate_keyboard(buttons)

    def test_row_too_wide(self) -> None:
        validator = KeyboardValidator()
        row = [
            CallbackButton(text=str(i), payload=str(i))
            for i in range(validator.max_width + 1)
        ]

        with pytest.raises(ValueError, match="too long"):
            validator.validate_row(row)

    def test_size_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="not allowed"):
            KeyboardValidator().validate_size(0)

    def test_valid_keyboard(self) -> None:
        validator = KeyboardValidator()

        assert validator.validate_keyboard([[CallbackButton(text="a", payload="a")]])


class TestKeyboardBuilder:
    def test_validates_initial_keyboard(self) -> None:
        row: list[InlineButtons] = [
            CallbackButton(text=str(i), payload=str(i))
            for i in range(KeyboardValidator.max_width + 1)
        ]

        with pytest.raises(ValueError, match="too long"):
            KeyboardBuilder([row])

    def test_row_splits_by_width(self) -> None:
        builder = KeyboardBuilder()
        buttons = [CallbackButton(text=str(i), payload=str(i)) for i in range(4)]

        builder.row(*buttons, width=2)

        assert len(builder.build()) == 2

    def test_add_fills_last_row_first(self) -> None:
        builder = KeyboardBuilder()
        builder.row(CallbackButton(text="a", payload="a"), width=2)

        builder.add(CallbackButton(text="b", payload="b"))

        assert len(builder.build()) == 1
        assert len(builder.build()[0]) == 2
