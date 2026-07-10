from typing import Any

import pytest

from maxo import Bot, Ctx
from tests.mocks import MockBot


@pytest.fixture
def bot() -> MockBot:
    return MockBot()


@pytest.fixture
def ctx(update: Any, bot: Bot) -> Ctx:
    ctx = Ctx({"update": update, "bot": bot})
    ctx["ctx"] = ctx
    return ctx
