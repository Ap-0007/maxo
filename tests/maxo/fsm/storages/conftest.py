from maxo.fsm.key_builder import StorageKey


def make_key(
    *,
    chat_id: int = -42,
    user_id: int = 42,
    bot_id: int = 1,
) -> StorageKey:
    return StorageKey(chat_id=chat_id, user_id=user_id, bot_id=bot_id)
