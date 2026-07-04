from magic_filter import F

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.link_preview import LinkPreview, LinkPreviewBase
from maxo.dialogs.widgets.text import Const


async def test_link_preview_base_returns_none(mock_manager: DialogManager) -> None:
    widget = LinkPreviewBase()

    assert await widget.render_link_preview({}, mock_manager) is None


async def test_link_preview_base_respects_when(mock_manager: DialogManager) -> None:
    widget = LinkPreviewBase(when=F["enabled"])

    assert await widget.render_link_preview({}, mock_manager) is None


async def test_link_preview_renders_url_and_disabled_flag(
    mock_manager: DialogManager,
) -> None:
    widget = LinkPreview(url=Const("https://example.com"), is_disabled=True)

    options = await widget.render_link_preview({}, mock_manager)

    assert options is not None
    assert options.url == "https://example.com"
    assert options.is_disabled is True


async def test_link_preview_without_url(mock_manager: DialogManager) -> None:
    widget = LinkPreview()

    options = await widget.render_link_preview({}, mock_manager)

    assert options is not None
    assert options.url is None
    assert options.is_disabled is False


async def test_link_preview_respects_when(mock_manager: DialogManager) -> None:
    widget = LinkPreview(url=Const("https://example.com"), when=F["enabled"])

    assert await widget.render_link_preview({}, mock_manager) is None
