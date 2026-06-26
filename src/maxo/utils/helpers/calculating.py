from maxo.enums import ChatType
from maxo.omit import Omittable, Omitted


def calculate_chat_id_and_user_id(
    chat_type: ChatType,
    chat_id: Omittable[int | None],
    user_id: Omittable[int | None],
) -> tuple[Omittable[int], Omittable[int]]:
    if chat_type is ChatType.CHAT:
        # Если мы в чате, то нам не надо отправлять сообщение юзеру,
        # поэтому остаётся только chat_id
        return chat_id or Omitted(), Omitted()
    if chat_type is ChatType.DIALOG:
        # Если мы в личке, то API хавает и чат, и юзера
        return chat_id or Omitted(), user_id or Omitted()
    if chat_type is ChatType.CHANNEL:
        # То же, что ChatType.CHAT
        return chat_id or Omitted(), Omitted()
    # ChatType.PRIVATE/GROUP/SUPERGROUP - алиасы значений выше,
    # поэтому сюда исполнение не доходит.
    msg = f"Неизвестный тип чата: {chat_type}"
    raise AssertionError(msg)
