from typing import Any, cast

import pytest

from maxo.dialogs.api.entities import ChatEvent, Context, MediaAttachment
from maxo.dialogs.api.protocols import DialogManager
from maxo.dialogs.widgets.media import DynamicMedia, Media, MediaScroll, StaticMedia
from maxo.dialogs.widgets.text import Format
from maxo.enums import AttachmentType
from maxo.fsm.state import State


class DummyManager:
    def __init__(self) -> None:
        self.widget_data: dict[
            str,
            dict[Any, Any] | list[Any] | int | str | float | None,
        ] = {}

    def current_context(self) -> Context:
        return Context(
            dialog_data={},
            start_data={},
            widget_data=self.widget_data,
            state=State(),
            _stack_id="_stack_id",
            _intent_id="_intent_id",
        )

    def is_preview(self) -> bool:
        return False


class StubMedia(Media):
    def __init__(self, token: str) -> None:
        super().__init__()
        self.token = token

    async def _render_media(
        self,
        data: dict[Any, Any],
        manager: Any,
    ) -> list[MediaAttachment]:
        return [MediaAttachment(AttachmentType.IMAGE, path=self.token)]


def chat_event() -> ChatEvent:
    # cast нужен, чтобы не создавать полный update для проверки media scroll.
    return cast(ChatEvent, object())


def manager() -> DialogManager:
    # cast нужен для легковесного объекта с минимальным набором полей протокола.
    return cast(DialogManager, DummyManager())


async def test_media_or_and_add() -> None:
    dialog_manager = manager()
    media = StubMedia("a") | StubMedia("b")
    multi = StubMedia("a") + StubMedia("b")

    assert await media.render_media({}, dialog_manager) == [
        MediaAttachment(AttachmentType.IMAGE, path="a"),
    ]
    assert await multi.render_media({}, dialog_manager) == [
        MediaAttachment(AttachmentType.IMAGE, path="a"),
        MediaAttachment(AttachmentType.IMAGE, path="b"),
    ]


async def test_static_and_dynamic_media() -> None:
    dialog_manager = manager()
    static_url = StaticMedia(url="https://example.com/image.png")
    static_path = StaticMedia(path="image.png")
    dynamic = DynamicMedia(
        lambda data: [MediaAttachment(AttachmentType.IMAGE, path=data["path"])],
    )

    assert (await static_url.render_media({}, dialog_manager))[
        0
    ].url == "https://example.com/image.png"
    assert (await static_path.render_media({}, dialog_manager))[0].path == "image.png"
    assert (await dynamic.render_media({"path": "dynamic.png"}, dialog_manager))[
        0
    ].path == "dynamic.png"


async def test_static_media_rejects_empty_sources() -> None:
    with pytest.raises(ValueError, match="Neither url nor path"):
        StaticMedia()


async def test_media_scroll_renders_selected_item() -> None:
    dialog_manager = manager()
    media = MediaScroll(
        items=["0.png", "1.png", "2.png"],
        media=StaticMedia(path=Format("/{item}")),
        id="scroll",
    )

    rendered = await media.render_media({}, dialog_manager)
    assert rendered[0].path == "/0.png"
    await media.set_page(event=chat_event(), page=2, manager=dialog_manager)
    rendered = await media.render_media({}, dialog_manager)
    assert rendered[0].path == "/2.png"
