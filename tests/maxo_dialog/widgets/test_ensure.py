from typing import Any

import pytest

from maxo.dialogs.api.exceptions import InvalidWidgetType
from maxo.dialogs.widgets.data import CompositeGetter, StaticGetter
from maxo.dialogs.widgets.input import CombinedInput, MessageInput, TextInput
from maxo.dialogs.widgets.kbd import Button, Group, Row
from maxo.dialogs.widgets.link_preview import LinkPreview
from maxo.dialogs.widgets.media import Media, StaticMedia
from maxo.dialogs.widgets.text import Const, Format, Multi
from maxo.dialogs.widgets.utils import (
    ensure_data_getter,
    ensure_input,
    ensure_keyboard,
    ensure_link_preview,
    ensure_media,
    ensure_text,
    ensure_widgets,
)


class TestEnsureText:
    def test_str_becomes_format(self) -> None:
        assert isinstance(ensure_text("{x}"), Format)

    def test_single_element_sequence_unwrapped(self) -> None:
        const = Const("a")

        assert ensure_text([const]) is const

    def test_many_become_multi(self) -> None:
        assert isinstance(ensure_text([Const("a"), Const("b")]), Multi)

    def test_widget_passthrough(self) -> None:
        const = Const("a")

        assert ensure_text(const) is const


class TestEnsureKeyboard:
    def test_single_element_sequence_unwrapped(self) -> None:
        button = Button(Const("b"), id="b")

        assert ensure_keyboard([button]) is button

    def test_many_become_group(self) -> None:
        keyboard = ensure_keyboard([Row(), Row()])

        assert isinstance(keyboard, Group)

    def test_widget_passthrough(self) -> None:
        row = Row()

        assert ensure_keyboard(row) is row


class TestEnsureInput:
    def test_empty_sequence_is_none(self) -> None:
        assert ensure_input([]) is None

    def test_single_element_sequence_unwrapped(self) -> None:
        text_input: TextInput[str] = TextInput(id="i")

        assert ensure_input([text_input]) is text_input

    def test_many_become_combined(self) -> None:
        inputs: list[Any] = [TextInput(id="a"), TextInput(id="b")]

        assert isinstance(ensure_input(inputs), CombinedInput)

    def test_callable_becomes_message_input(self) -> None:
        async def handler(*_args: Any, **_kwargs: Any) -> None: ...

        assert isinstance(ensure_input(handler), MessageInput)

    def test_widget_passthrough(self) -> None:
        text_input: TextInput[str] = TextInput(id="i")

        assert ensure_input(text_input) is text_input


class TestEnsureMedia:
    def test_widget_passthrough(self) -> None:
        media = StaticMedia(url="http://e.com/a.png")

        assert ensure_media(media) is media

    def test_single_element_sequence_unwrapped(self) -> None:
        media = StaticMedia(url="http://e.com/a.png")

        assert ensure_media([media]) is media

    def test_many_become_multi_media(self) -> None:
        media = [
            StaticMedia(url="http://e.com/a.png"),
            StaticMedia(url="http://e.com/b.png"),
        ]

        assert isinstance(ensure_media(media), Media)

    def test_empty_sequence_becomes_empty_media(self) -> None:
        assert isinstance(ensure_media([]), Media)


class TestEnsureLinkPreview:
    def test_widget_passthrough(self) -> None:
        preview = LinkPreview(url=Const("http://e.com"))

        assert ensure_link_preview(preview) is preview

    def test_single_element_sequence_unwrapped(self) -> None:
        preview = LinkPreview(url=Const("http://e.com"))

        assert ensure_link_preview([preview]) is preview

    def test_empty_sequence_is_none(self) -> None:
        assert ensure_link_preview([]) is None

    def test_many_rejected(self) -> None:
        previews = [
            LinkPreview(url=Const("http://e.com")),
            LinkPreview(url=Const("http://e.org")),
        ]

        with pytest.raises(ValueError, match="Only one link preview"):
            ensure_link_preview(previews)


class TestEnsureWidgets:
    def test_splits_widgets_by_type(self) -> None:
        async def handler(*_args: Any, **_kwargs: Any) -> None: ...

        text, keyboard, input_, media, link_preview = ensure_widgets(
            [
                "hello {name}",
                Const("a"),
                Row(),
                handler,
                StaticMedia(url="http://e.com/a.png"),
                LinkPreview(url=Const("http://e.com")),
            ],
        )

        assert isinstance(text, Multi)
        assert keyboard is not None
        assert isinstance(input_, MessageInput)
        assert isinstance(media, Media)
        assert link_preview is not None

    def test_unknown_widget_type(self) -> None:
        with pytest.raises(InvalidWidgetType, match="Cannot add widget"):
            ensure_widgets([object()])  # type: ignore[list-item]


class TestEnsureDataGetter:
    def test_none_becomes_empty_static(self) -> None:
        assert isinstance(ensure_data_getter(None), StaticGetter)

    def test_dict_becomes_static(self) -> None:
        assert isinstance(ensure_data_getter({"a": 1}), StaticGetter)

    def test_callable_passthrough(self) -> None:
        async def getter(**_kwargs: Any) -> dict[Any, Any]:
            return {}

        assert ensure_data_getter(getter) is getter

    def test_list_becomes_composite(self) -> None:
        assert isinstance(ensure_data_getter([{"a": 1}, {"b": 2}]), CompositeGetter)

    def test_tuple_becomes_composite(self) -> None:
        assert isinstance(ensure_data_getter(({"a": 1},)), CompositeGetter)

    def test_unknown_getter_type(self) -> None:
        with pytest.raises(InvalidWidgetType, match="Cannot add data getter"):
            ensure_data_getter(42)  # type: ignore[arg-type]
