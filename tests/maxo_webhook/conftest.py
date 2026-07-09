from ipaddress import IPv4Address

import pytest

from maxo import Bot
from tests.constants import TOKEN


def make_bot(token: str = TOKEN) -> Bot:
    return Bot(token=token, warming_up=False)


@pytest.fixture
def bot() -> Bot:
    return make_bot()


@pytest.fixture
def localhost_ip() -> IPv4Address:
    return IPv4Address("127.0.0.1")
