from typing import Any

from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities import MarkupVariant
from maxo.dialogs.api.internal.widgets import (
    MarkupFactory,
    RawKeyboard,
)
from maxo.dialogs.utils import add_intent_id


class InlineKeyboardFactory(MarkupFactory):
    async def render_markup(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
        keyboard: RawKeyboard,
    ) -> MarkupVariant:
        # TODO: Validate buttons
        add_intent_id(keyboard, manager.current_context().id)
        return keyboard
