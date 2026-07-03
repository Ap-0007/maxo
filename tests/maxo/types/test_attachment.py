import pytest

from maxo.types import Attachment


def test_abstract_to_request() -> None:
    class MyAttachment(Attachment):
        pass

    with pytest.raises(NotImplementedError):
        _ = MyAttachment(type=None).to_request()
