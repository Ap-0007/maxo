import pytest

from maxo.enums.attachment_type import AttachmentType
from maxo.types import Attachment
from maxo.types.attachments import AttachmentsRequests


def test_abstract_to_request() -> None:
    class MyAttachment(Attachment):
        def to_request(self) -> AttachmentsRequests:
            return Attachment.to_request(self)

    with pytest.raises(NotImplementedError):
        _ = MyAttachment(type=AttachmentType.IMAGE).to_request()
