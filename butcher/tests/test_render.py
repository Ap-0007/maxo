"""Тесты формы сгенерированного кода."""

from butcher.profile import Enum, MaxoDocument, Method, Model
from butcher.render import docs, enums, methods, types, unions


def _model(document: MaxoDocument, name: str) -> Model:
    return next(item for item in document.models if item.name == name)


def _enum(document: MaxoDocument, name: str) -> Enum:
    return next(item for item in document.enums if item.name == name)


def _method(document: MaxoDocument, name: str) -> Method:
    return next(item for item in document.methods if item.name == name)


def test_model_declares_base_and_tag_default(document: MaxoDocument) -> None:
    source = types.render(_model(document, "PhotoAttachment"))
    assert "class PhotoAttachment(Attachment):" in source
    assert "    type: AttachmentType = AttachmentType.IMAGE" in source
    assert "from maxo.types.attachment import Attachment" in source


def test_update_declares_bare_type_assignment(document: MaxoDocument) -> None:
    source = types.render(_model(document, "MessageCreated"))
    assert "class MessageCreated(MaxUpdate, MessageMethodsFacade):" in source
    assert "    type = UpdateType.MESSAGE_CREATED" in source


def test_model_renders_unsafe_property(document: MaxoDocument) -> None:
    source = types.render(_model(document, "Message"))
    assert "    def unsafe_url(self) -> str:" in source
    assert '            attr="url",' in source


def test_model_docstring_has_args_block(document: MaxoDocument) -> None:
    source = types.render(_model(document, "Message"))
    assert "    Args:" in source
    assert "        timestamp: Время создания сообщения" in source


def test_enum_renders_extras(document: MaxoDocument) -> None:
    source = enums.render(_enum(document, "AttachmentType"))
    assert 'TEXT = "text"  # Самодельное поле' in source
    assert "    IMAGE = 'image'" in source or '    IMAGE = "image"' in source
    assert "    PHOTO = IMAGE" in source
    assert "ContentType: TypeAlias = AttachmentType  # Подражание aiogram" in source


def test_enum_single_line_description_stays_inline(document: MaxoDocument) -> None:
    source = enums.render(_enum(document, "AttachmentType"))
    assert '    """Вложение"""' in source


def test_method_renders_markers_and_dunders(document: MaxoDocument) -> None:
    source = methods.render(_method(document, "SendMessage"))
    assert "class SendMessage(MaxoMethod[Message]):" in source
    assert '    __url__ = "messages"' in source
    assert '    __method__ = "post"' in source
    assert "    chat_id: Query[Omittable[int]] = Omitted()" in source
    assert "    text: Body[str | None] = None" in source
    assert "    Источник: https://dev.max.ru/docs-api/methods/POST/messages" in source


def test_method_path_placeholder_is_snake_case(document: MaxoDocument) -> None:
    source = methods.render(_method(document, "GetChat"))
    assert '    __url__ = "chats/{chat_id}"' in source
    assert "    chat_id: Path[int]" in source


def test_unions_render_without_blank_lines(document: MaxoDocument) -> None:
    attachments = next(item for item in document.unions if item.module == "attachments")
    source = unions.render(attachments)
    assert "MediaAttachments = PhotoAttachment | VideoAttachment\n" in source
    assert "\n\nAttachments" not in source.split("MediaAttachments", 1)[1]


def test_updates_alias_is_annotated(document: MaxoDocument) -> None:
    updates = next(item for item in document.unions if item.module == "updates")
    source = unions.render(updates)
    assert "from typing import TypeAlias" in source
    assert "Updates: TypeAlias = MessageCreated" in source


def test_links_become_absolute() -> None:
    assert docs.clean("см. [тут](/docs-api#Якорь)") == (
        "см. [тут](https://dev.max.ru/docs-api#Якорь)"
    )
    assert docs.clean("см. [тут](/docs/webapps/bridge)") == (
        "см. [тут](https://dev.max.ru/docs/webapps/bridge)"
    )
    # Абсолютные ссылки не трогаем.
    assert docs.clean("[a](https://example.com)") == "[a](https://example.com)"


def test_dashes_are_normalized() -> None:
    assert docs.clean("а — б – в") == "а - б - в"
