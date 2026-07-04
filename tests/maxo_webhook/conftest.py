from ipaddress import IPv4Address

import pytest

from maxo import Bot

TOKEN = "f9LHod"  # noqa: S105


def make_bot(token: str = TOKEN) -> Bot:
    return Bot(token=token, warming_up=False)


@pytest.fixture
def bot() -> Bot:
    return Bot(token=TOKEN, warming_up=False)


@pytest.fixture
def localhost_ip() -> IPv4Address:
    return IPv4Address("127.0.0.1")
