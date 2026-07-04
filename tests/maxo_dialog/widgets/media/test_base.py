from typing import Any

from magic_filter import F

from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities import MediaAttachment
from maxo.dialogs.widgets.common import WhenCondition
from maxo.dialogs.widgets.media import Media, MultiMedia
from maxo.dialogs.widgets.media.base import Or
from maxo.enums import AttachmentType


class Static(Media):
    def __init__(self, path: str, when: WhenCondition = None) -> None:
        super().__init__(when=when)
        self.path = path

    async def _render_media(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> list[MediaAttachment]:
        return [MediaAttachment(AttachmentType.IMAGE, path=self.path)]


async def test_or(mock_manager: DialogManager) -> None:
    text = Static("a") | Static("b")
    res = await text.render_media({}, mock_manager)
    assert res == [MediaAttachment(AttachmentType.IMAGE, path="a")]


async def test_or_condition(mock_manager: DialogManager) -> None:
    text = Static("A", when=F["a"]) | Static("B", when=F["b"]) | Static("C")
    res = await text.render_media({"a": True}, mock_manager)
    assert res == [MediaAttachment(AttachmentType.IMAGE, path="A")]
    res = await text.render_media({"b": True}, mock_manager)
    assert res == [MediaAttachment(AttachmentType.IMAGE, path="B")]
    res = await text.render_media({}, mock_manager)
    assert res == [MediaAttachment(AttachmentType.IMAGE, path="C")]


async def test_add_creates_multimedia(mock_manager: DialogManager) -> None:
    media = Static("a") + Static("b")
    assert isinstance(media, MultiMedia)

    res = await media.render_media({}, mock_manager)
    assert res == [
        MediaAttachment(AttachmentType.IMAGE, path="a"),
        MediaAttachment(AttachmentType.IMAGE, path="b"),
    ]


async def test_multimedia_iadd(mock_manager: DialogManager) -> None:
    media = MultiMedia(Static("a"), Static("b"))
    media += Static("c")

    res = await media.render_media({}, mock_manager)
    assert len(res) == 3
    assert res[2] == MediaAttachment(AttachmentType.IMAGE, path="c")


async def test_multimedia_nested_with_true_condition(
    mock_manager: DialogManager,
) -> None:
    # MultiMedia с true_condition должен разворачиваться при вложении
    inner = MultiMedia(Static("a"), Static("b"))
    outer = inner + Static("c")

    assert isinstance(outer, MultiMedia)
    assert len(outer.media) == 3


async def test_multimedia_radd(mock_manager: DialogManager) -> None:
    media = Static("a") + MultiMedia(Static("b"), Static("c"))

    res = await media.render_media({}, mock_manager)
    assert len(res) == 3
    assert res[0] == MediaAttachment(AttachmentType.IMAGE, path="a")


async def test_multimedia_find(mock_manager: DialogManager) -> None:
    # Media виджеты не имеют id, find всегда возвращает None
    widget_a = Static("a")
    widget_b = Static("b")

    media = MultiMedia(widget_a, widget_b)

    # find возвращает None, так как Media не реализует поиск по id
    found = media.find("any_id")
    assert found is None


async def test_or_ior(mock_manager: DialogManager) -> None:
    media = Or(Static("a"))
    media |= Static("b")

    assert len(media.widgets) == 2


async def test_or_nested_operations(mock_manager: DialogManager) -> None:
    # Or должен разворачивать вложенные Or
    inner_or = Static("a") | Static("b")
    outer_or = inner_or | Static("c")

    assert isinstance(outer_or, Or)
    assert len(outer_or.widgets) == 3


async def test_or_ror(mock_manager: DialogManager) -> None:
    media = Static("a") | Or(Static("b"), Static("c"))

    res = await media.render_media({}, mock_manager)
    assert res == [MediaAttachment(AttachmentType.IMAGE, path="a")]


async def test_media_when_condition_false(mock_manager: DialogManager) -> None:
    media = Static("a", when=F["show"])

    res = await media.render_media({"show": False}, mock_manager)
    assert res == []


async def test_or_returns_empty_when_all_fail(mock_manager: DialogManager) -> None:
    media = (
        Static("a", when=F["show_a"])
        | Static("b", when=F["show_b"])
        | Static("c", when=F["show_c"])
    )

    res = await media.render_media({}, mock_manager)
    assert res == []
