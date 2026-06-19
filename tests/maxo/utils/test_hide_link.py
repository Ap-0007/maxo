from maxo.types.share_attachment import ShareAttachment
from maxo.types.share_attachment_request import ShareAttachmentRequest
from maxo.utils.hide_link import hide_link


def test_hide_link_returns_share_attachment() -> None:
    att = hide_link("https://example.com")
    assert isinstance(att, ShareAttachment)
    assert att.payload.url == "https://example.com"


def test_hide_link_to_request_keeps_url() -> None:
    req = hide_link("https://example.com").to_request()
    assert isinstance(req, ShareAttachmentRequest)
    assert req.payload.url == "https://example.com"
