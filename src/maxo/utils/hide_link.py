from maxo.types.share_attachment import ShareAttachment


def hide_link(url: str) -> ShareAttachment:
    """
    Превью-ссылка без видимого текста (Max-аналог aiogram hide_link).

    В отличие от aiogram возвращает не строку для вставки в текст, а
    `ShareAttachment` - передайте его в `attachments` при отправке сообщения.
    Макс отрисует предпросмотр ссылки, не показывая сам URL в тексте.

    Args:
        url: ссылка, для которой нужен предпросмотр.

    """
    return ShareAttachment.factory(url=url)
