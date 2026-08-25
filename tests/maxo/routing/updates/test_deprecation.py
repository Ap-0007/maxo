# ruff: noqa: PLC0415
import importlib

import pytest

from maxo import types


def test_deprecation_warning() -> None:
    import maxo.routing.updates

    with pytest.warns(
        DeprecationWarning,
        match="Апдейты были перенесены из `maxo.routing.updates` в `maxo.types`",
    ):
        importlib.reload(maxo.routing.updates)


def test_all_updates_are_reexported_from_types() -> None:
    import maxo.routing.updates as updates

    for name in updates.__all__:
        assert hasattr(updates, name)
        assert getattr(updates, name) is getattr(types, name)


@pytest.mark.parametrize(
    ("module_name", "names"),
    {
        "base": ("BaseUpdate", "MaxUpdate"),
        "bot_added_to_chat": ("BotAddedToChat",),
        "bot_removed_from_chat": ("BotRemovedFromChat",),
        "bot_started": ("BotStarted",),
        "bot_stopped": ("BotStopped",),
        "chat_title_changed": ("ChatTitleChanged",),
        "comment_created": ("CommentCreated",),
        "comment_edited": ("CommentEdited",),
        "comment_removed": ("CommentRemoved",),
        "dialog_cleared": ("DialogCleared",),
        "dialog_muted": ("DialogMuted",),
        "dialog_removed": ("DialogRemoved",),
        "dialog_unmuted": ("DialogUnmuted",),
        "error": ("ErrorEvent",),
        "message_callback": ("CallbackQuery", "MessageCallback"),
        "message_created": ("MessageCreated",),
        "message_edited": ("MessageEdited",),
        "message_removed": ("MessageRemoved",),
        "updates": ("Updates",),
        "user_added_to_chat": ("UserAddedToChat",),
        "user_removed_from_chat": ("UserRemovedFromChat",),
    }.items(),
)
def test_deep_import_shims_reexport_from_types(
    module_name: str,
    names: tuple[str, ...],
) -> None:
    module = importlib.import_module(f"maxo.routing.updates.{module_name}")

    assert module.__all__ == names
    for name in names:
        assert getattr(module, name) is getattr(types, name)
