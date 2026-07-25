"""Тесты трансформаций maxo-профиля."""

import json
from pathlib import Path

import pytest

from butcher import overrides
from butcher.profile import Enum, MaxoDocument, Method, Model, build_profile
from butcher.spec import load
from butcher.tests.conftest import SPEC


def _model(document: MaxoDocument, name: str) -> Model:
    return next(item for item in document.models if item.name == name)


def _enum(document: MaxoDocument, name: str) -> Enum:
    return next(item for item in document.enums if item.name == name)


def _method(document: MaxoDocument, name: str) -> Method:
    return next(item for item in document.methods if item.name == name)


def test_inheritance_keeps_only_own_fields(document: MaxoDocument) -> None:
    base = _model(document, "Attachment")
    assert base.base == "MaxoType"
    assert [f.name for f in base.fields] == ["type"]

    subtype = _model(document, "PhotoAttachment")
    assert subtype.base == "Attachment"
    assert {f.name for f in subtype.fields} == {"type", "payload"}


def test_discriminator_becomes_enum(document: MaxoDocument) -> None:
    enum = _enum(document, "AttachmentType")
    assert enum.description == "Вложение"
    assert [(m.name, m.value) for m in enum.members] == [
        ("IMAGE", "image"),
        ("VIDEO", "video"),
    ]


def test_base_tag_field_is_typed_by_enum(document: MaxoDocument) -> None:
    tag = next(f for f in _model(document, "Attachment").fields if f.name == "type")
    assert tag.annotation == "AttachmentType"
    assert tag.default is None


def test_subtype_tag_field_gets_enum_default(document: MaxoDocument) -> None:
    tag = next(
        f for f in _model(document, "PhotoAttachment").fields if f.name == "type"
    )
    assert tag.annotation == "AttachmentType"
    assert tag.default == "AttachmentType.IMAGE"
    assert not tag.bare_assignment


def test_updates_lose_suffix_and_inherit_max_update(document: MaxoDocument) -> None:
    update = _model(document, "MessageCreated")
    assert update.base == "MaxUpdate"
    # База апдейтов ведётся вручную, её файл не генерируется.
    assert all(item.name != "Update" for item in document.models)


def test_update_tag_is_a_bare_assignment(document: MaxoDocument) -> None:
    # `type` объявлен `ClassVar` в `MaxUpdate`, наследник только присваивает значение.
    tag = next(f for f in _model(document, "MessageCreated").fields if f.name == "type")
    assert tag.bare_assignment
    assert tag.default == "UpdateType.MESSAGE_CREATED"


def test_int64_timestamp_becomes_datetime(document: MaxoDocument) -> None:
    fields = {f.name: f for f in _model(document, "Message").fields}
    assert fields["timestamp"].annotation == "datetime"
    # У `seq` тот же формат, но описание не про время - остаётся int.
    assert fields["seq"].annotation == "int"


def test_base_reference_is_replaced_by_union_alias(document: MaxoDocument) -> None:
    attachments = next(
        f for f in _model(document, "Message").fields if f.name == "attachments"
    )
    assert attachments.annotation == "list[Attachments] | None"


def test_union_files_are_built_from_discriminator(document: MaxoDocument) -> None:
    attachments = next(item for item in document.unions if item.module == "attachments")
    names = {alias.name: alias.members for alias in attachments.aliases}
    # В этой спеке есть только photo и video, а оба входят в MediaAttachments,
    # поэтому Attachments сводится к нему одному.
    assert names["MediaAttachments"] == ("PhotoAttachment", "VideoAttachment")
    assert names["Attachments"] == ("MediaAttachments",)
    updates = next(item for item in document.unions if item.module == "updates")
    assert updates.aliases[0].members == ("MessageCreated",)
    assert updates.aliases[0].annotate


def test_union_skips_members_absent_from_spec(document: MaxoDocument) -> None:
    # В таблице MediaAttachments перечислены ещё audio и file, но их в спеке нет.
    attachments = next(item for item in document.unions if item.module == "attachments")
    members = next(
        a for a in attachments.aliases if a.name == "MediaAttachments"
    ).members
    assert "AudioAttachment" not in members


def test_union_file_without_base_is_not_generated(document: MaxoDocument) -> None:
    # Спека не описывает `Button`, поэтому `buttons.py` не собирается.
    assert all(item.module != "buttons" for item in document.unions)


def test_skipped_schema_is_not_generated(document: MaxoDocument) -> None:
    assert all(item.name != "ChatButton" for item in document.models)


def test_enum_extras_are_applied(document: MaxoDocument) -> None:
    enum = _enum(document, "AttachmentType")
    assert [m.name for m in enum.extras.leading] == ["TEXT", "UNKNOWN"]
    assert enum.exported_names == ("AttachmentType", "ContentType")


def test_method_url_uses_snake_case_placeholders(document: MaxoDocument) -> None:
    method = _method(document, "GetChat")
    assert method.url == "chats/{chat_id}"
    assert method.http_method == "get"
    assert method.doc_link.endswith("/methods/GET/chats/-chatId-")


def test_method_ignores_spec_defaults(document: MaxoDocument) -> None:
    # `disable_link_preview` объявлен с `default: false`, но у maxo необязательный
    # параметр - это `Omitted()`, а не подставленное значение.
    field = next(
        f
        for f in _method(document, "SendMessage").fields
        if f.name.startswith("disable")
    )
    assert field.omittable
    assert field.default is None


def test_method_parameter_timestamp_becomes_datetime(document: MaxoDocument) -> None:
    # То же правило, что и для полей моделей: целое с описанием про время - datetime.
    fields = {f.name: f for f in _method(document, "SendMessage").fields}
    assert fields["from_"].annotation == "datetime"
    # У `chat_id` тот же тип, но описание не про время - остаётся int.
    assert fields["chat_id"].annotation == "int"


def test_method_body_fields_keep_descriptions(document: MaxoDocument) -> None:
    text = next(f for f in _method(document, "SendMessage").fields if f.name == "text")
    assert text.marker == "Body"
    assert text.description == "Текст сообщения"
    assert text.optional
    assert not text.omittable


def test_method_body_widens_attachment_requests(document: MaxoDocument) -> None:
    attachments = next(
        f for f in _method(document, "SendMessage").fields if f.name == "attachments"
    )
    assert attachments.annotation == "list[AttachmentsRequests | Attachments] | None"


def test_skipped_operation_is_not_generated(document: MaxoDocument) -> None:
    # `GetChats` ведётся вручную; в этой спеке его нет, но таблица не должна ломаться.
    assert all(item.name != "GetChats" for item in document.methods)


def test_unsafe_properties_only_for_absent_values(document: MaxoDocument) -> None:
    fields = {f.name: f for f in _model(document, "Message").fields}
    assert fields["url"].unsafe
    assert not fields["timestamp"].unsafe


def test_model_field_ignores_spec_default(document: MaxoDocument) -> None:
    # У поля есть `default: true`, но оно необязательное - в maxo это `Omitted()`,
    # а не `= True` (дефолты свагера игнорируем и в моделях, как в методах).
    notify = next(f for f in _model(document, "Message").fields if f.name == "notify")
    assert notify.omittable
    assert notify.default is None


def test_model_field_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # MODEL_FIELD_OVERRIDES перекрывает тип/омиттабельность и добавляет коммент.
    monkeypatch.setitem(
        overrides.MODEL_FIELD_OVERRIDES,
        ("Message", "url"),
        overrides.FieldOverride(omittable=True, comment="type: ignore[assignment]"),
    )
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(SPEC), encoding="utf-8")
    document = build_profile(load(str(path)))
    url = next(f for f in _model(document, "Message").fields if f.name == "url")
    assert url.omittable
    assert url.comment == "type: ignore[assignment]"


def test_method_field_type_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # METHOD_FIELD_TYPES перекрывает тип поля метода, минуя генератор (нужно
    # там, где свагер описан неверно и тип выводится в `Any`).
    monkeypatch.setitem(
        overrides.METHOD_FIELD_TYPES,
        ("SendMessage", "text"),
        "list[int]",
    )
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(SPEC), encoding="utf-8")
    document = build_profile(load(str(path)))
    text = next(f for f in _method(document, "SendMessage").fields if f.name == "text")
    assert text.annotation == "list[int]"
