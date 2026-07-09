import pytest

from maxo.fsm.key_builder import (
    DESTINY_DEFAULT,
    DefaultKeyBuilder,
    StorageKey,
    StorageKeyType,
)

PREFIX = "test"
BOT_ID = 42
CHAT_ID = -1
USER_ID = 2


@pytest.mark.parametrize(
    ("key_builder", "type_", "result"),
    [
        (
            DefaultKeyBuilder(prefix=PREFIX),
            None,
            f"{PREFIX}:{CHAT_ID}:{USER_ID}",
        ),
        (
            DefaultKeyBuilder(prefix=PREFIX),
            StorageKeyType.DATA,
            f"{PREFIX}:{CHAT_ID}:{USER_ID}:data",
        ),
        (
            DefaultKeyBuilder(prefix=PREFIX, with_bot_id=True),
            StorageKeyType.STATE,
            f"{PREFIX}:{CHAT_ID}:{USER_ID}:{BOT_ID}:state",
        ),
        (
            DefaultKeyBuilder(prefix=PREFIX, with_destiny=True),
            StorageKeyType.LOCK,
            f"{PREFIX}:{CHAT_ID}:{USER_ID}:{DESTINY_DEFAULT}:lock",
        ),
        (
            DefaultKeyBuilder(
                prefix=PREFIX,
                separator=";",
                with_bot_id=True,
                with_destiny=True,
            ),
            StorageKeyType.DATA,
            f"{PREFIX};{CHAT_ID};{USER_ID};{BOT_ID};{DESTINY_DEFAULT};data",
        ),
    ],
)
def test_default_key_builder(
    key_builder: DefaultKeyBuilder,
    type_: StorageKeyType | None,
    result: str,
) -> None:
    key = StorageKey(chat_id=CHAT_ID, user_id=USER_ID, bot_id=BOT_ID)

    assert key_builder.build(key, type_) == result


def test_default_key_builder_rejects_custom_destiny_without_flag() -> None:
    key_builder = DefaultKeyBuilder()
    key = StorageKey(
        chat_id=CHAT_ID,
        user_id=USER_ID,
        bot_id=BOT_ID,
        destiny="custom",
    )

    with pytest.raises(ValueError, match="with_destiny=True"):
        key_builder.build(key, StorageKeyType.DATA)


def test_storage_key_can_be_chatless_or_userless() -> None:
    key_builder = DefaultKeyBuilder(prefix=PREFIX)
    key = StorageKey(bot_id=BOT_ID)

    assert key_builder.build(key) == f"{PREFIX}:None:None"
