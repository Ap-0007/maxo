import pytest

from maxo.utils.auth_widget import check_integrity, check_signature

TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
HASH = "c303db2b5a06fe41d23a9b14f7c545cfc11dcc7473c07c9c5034ae60062461ce"


@pytest.fixture
def auth_widget_data() -> dict[str, str]:
    return {
        "id": "42",
        "first_name": "John",
        "last_name": "Smith",
        "username": "username",
        "photo_url": "https://t.me/i/userpic/320/picname.jpg",
        "auth_date": "1565810688",
        "hash": HASH,
    }


def test_check_integrity_ok(auth_widget_data: dict[str, str]) -> None:
    assert check_integrity(TOKEN, auth_widget_data) is True


def test_check_integrity_fail(auth_widget_data: dict[str, str]) -> None:
    auth_widget_data.pop("username")

    assert check_integrity(TOKEN, auth_widget_data) is False


def test_check_signature_ok() -> None:
    assert (
        check_signature(
            TOKEN,
            HASH,
            id="42",
            first_name="John",
            last_name="Smith",
            username="username",
            photo_url="https://t.me/i/userpic/320/picname.jpg",
            auth_date="1565810688",
        )
        is True
    )
