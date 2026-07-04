from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities import MediaAttachment
from maxo.dialogs.widgets.common import WhenCondition
from maxo.dialogs.widgets.media import Media
from maxo.enums import AttachmentType


class Static(Media):
    def __init__(self, path: str, when: WhenCondition = None):
        super().__init__(when=when)
        self.path = path

    async def _render_media(
        self,
        data,
        manager: DialogManager,
    ) -> MediaAttachment:
        return MediaAttachment(AttachmentType.PHOTO, path=self.path)


async def test_or(mock_manager: DialogManager) -> None:
    text = Static("a") | Static("b")
    res = await text.render_media({}, mock_manager)
    assert res == MediaAttachment(AttachmentType.PHOTO, path="a")


async def test_or_condition(mock_manager: DialogManager) -> None:
    text = (
        Static("A", when=lambda data, manager: bool(data.get("a")))
        | Static("B", when=lambda data, manager: bool(data.get("b")))
        | Static("C")
    )
    res = await text.render_media({"a": True}, mock_manager)
    assert res == MediaAttachment(AttachmentType.PHOTO, path="A")
    res = await text.render_media({"b": True}, mock_manager)
    assert res == MediaAttachment(AttachmentType.PHOTO, path="B")
    res = await text.render_media({}, mock_manager)
    assert res == MediaAttachment(AttachmentType.PHOTO, path="C")
