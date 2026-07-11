from ipaddress import IPv4Address

import pytest

from maxo import Bot
from tests.factories import make_bot


@pytest.fixture
def bot() -> Bot:
    return make_bot()


@pytest.fixture
def localhost_ip() -> IPv4Address:
    return IPv4Address("127.0.0.1")
