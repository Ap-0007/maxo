from typing import Any

import pytest

from maxo.dialogs.api.entities import MediaAttachment
from maxo.dialogs.widgets.media import DynamicMedia, Media, MediaScroll, StaticMedia
from maxo.dialogs.widgets.text import Format
from maxo.enums import AttachmentType


class DummyManager:
    def __init__(self) -> None:
        self.widget_data: dict[str, int] = {}

    def current_context(self) -> Any:
        return self

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


async def test_media_or_and_add() -> None:
    manager = DummyManager()
    media = StubMedia("a") | StubMedia("b")
    multi = StubMedia("a") + StubMedia("b")

    assert await media.render_media({}, manager) == [
        MediaAttachment(AttachmentType.IMAGE, path="a"),
    ]
    assert await multi.render_media({}, manager) == [
        MediaAttachment(AttachmentType.IMAGE, path="a"),
        MediaAttachment(AttachmentType.IMAGE, path="b"),
    ]


async def test_static_and_dynamic_media() -> None:
    manager = DummyManager()
    static_url = StaticMedia(url="https://example.com/image.png")
    static_path = StaticMedia(path="image.png")
    dynamic = DynamicMedia(
        lambda data: [MediaAttachment(AttachmentType.IMAGE, path=data["path"])],
    )

    assert (await static_url.render_media({}, manager))[
        0
    ].url == "https://example.com/image.png"
    assert (await static_path.render_media({}, manager))[0].path == "image.png"
    assert (await dynamic.render_media({"path": "dynamic.png"}, manager))[
        0
    ].path == "dynamic.png"


async def test_static_media_rejects_empty_sources() -> None:
    with pytest.raises(ValueError, match="Neither url nor path"):
        StaticMedia()


async def test_media_scroll_renders_selected_item() -> None:
    manager = DummyManager()
    media = MediaScroll(
        items=["0.png", "1.png", "2.png"],
        media=StaticMedia(path=Format("/{item}")),
        id="scroll",
    )

    rendered = await media.render_media({}, manager)
    assert rendered[0].path == "/0.png"
    await media.set_page(event=object(), page=2, manager=manager)
    rendered = await media.render_media({}, manager)
    assert rendered[0].path == "/2.png"
