from typing import Any

from maxo import Bot
from maxo.types import BotInfo
from tests.constants import BOT_ID, NOW, TOKEN


def make_bot(token: str = TOKEN, **kwargs: Any) -> Bot:
    return Bot(token=token, warming_up=False, **kwargs)


def make_bot_info(
    user_id: int = BOT_ID,
    username: str = "testbot",
    first_name: str = "Test",
) -> BotInfo:
    return BotInfo(
        user_id=user_id,
        is_bot=True,
        first_name=first_name,
        username=username,
        last_activity_time=NOW,
    )
