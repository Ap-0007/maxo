from datetime import UTC, datetime
from typing import Any

import pytest

from maxo.dialogs.widgets.kbd import Button, Clipboard, Group, Keyboard, Url, WebApp
from maxo.dialogs.widgets.text import Const, Format, Multi
from maxo.routing.updates import MessageCallback
from maxo.types import (
    Callback,
    CallbackButton,
    LinkButton,
    OpenAppButton,
    User,
)


class DummyManager:
    def __init__(self, preview: bool = False) -> None:
        self.preview = preview

    def is_preview(self) -> bool:
        return self.preview


class DummyDialog:
    pass


class DummyButton(Keyboard):
    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: Any,
    ) -> list[list[CallbackButton]]:
        return [[CallbackButton(text="stub", payload=self.widget_id or "stub")]]


@pytest.mark.asyncio
async def test_text_rendering_and_combinators() -> None:
    manager = DummyManager()

    assert await Const("Hello").render_text({}, manager) == "Hello"
    assert await Format("Hello, {name}!").render_text({"name": "Tishka"}, manager) == (
        "Hello, Tishka!"
    )
    assert await (Const("Hello") + " " + Const("world")).render_text({}, manager) == (
        "Hello world"
    )
    assert await (Const("A") | Const("B")).render_text({}, manager) == "A"
    assert await Multi(Const("A"), Const(""), Const("B"), sep=" ").render_text(
        {},
        manager,
    ) == "A B"


@pytest.mark.asyncio
async def test_format_preview_mode_uses_stub_data() -> None:
    manager = DummyManager(preview=True)

    assert await Format("Hello, {name:>5}!").render_text({"name": "X"}, manager) == (
        "Hello,     X!"
    )


@pytest.mark.asyncio
async def test_keyboard_rendering_and_callback_routing() -> None:
    manager = DummyManager()
    dialog = DummyDialog()
    button = Button(Const("Click"), id="btn")
    url = Url(Const("Open"), Const("https://example.com"))
    web_app = WebApp(Const("App"), Const("bot"))
    clipboard = Clipboard(Const("Copy"), Const("payload"))
    group = Group(button, url, web_app, clipboard)
    custom = DummyButton(id="custom")

    keyboard = await button.render_keyboard({}, manager)
    assert keyboard[0][0].payload == "btn"

    url_keyboard = await url.render_keyboard({}, manager)
    assert isinstance(url_keyboard[0][0], LinkButton)

    web_app_keyboard = await web_app.render_keyboard({}, manager)
    assert isinstance(web_app_keyboard[0][0], OpenAppButton)

    group_keyboard = await group.render_keyboard({}, manager)
    assert len(group_keyboard) == 4

    assert custom.callback_prefix() == "custom:"
    assert custom._own_payload() == "custom"
    assert custom._item_payload("42") == "custom:42"

    callback = MessageCallback(
        callback=Callback(
            callback_id="cb",
            timestamp=datetime.now(UTC),
            user=User(
                user_id=1,
                first_name="Alice",
                is_bot=False,
                last_activity_time=datetime.now(UTC),
            ),
            payload="custom",
        ),
        timestamp=datetime.now(UTC),
    )
    assert await custom.process_callback(callback, dialog, manager) is False
