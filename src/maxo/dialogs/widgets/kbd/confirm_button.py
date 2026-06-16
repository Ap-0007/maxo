from collections.abc import Awaitable, Callable
from typing import Any

from maxo.dialogs import DialogManager, DialogProtocol
from maxo.dialogs.api.internal import RawKeyboard, TextWidget
from maxo.dialogs.utils import remove_intent_id
from maxo.dialogs.widgets.common import WhenCondition
from maxo.dialogs.widgets.kbd import Keyboard
from maxo.dialogs.widgets.widget_event import (
    WidgetEventProcessor,
    ensure_event_processor,
)
from maxo.routing.updates import MessageCallback
from maxo.types import CallbackButton

OnClick = Callable[[MessageCallback, "ConfirmButton", DialogManager], Awaitable]


class ConfirmButton(Keyboard):
    def __init__(
        self,
        id: str,
        primary_text: TextWidget,
        confirm_text: TextWidget,
        cancel_text: TextWidget,
        are_you_sure_text: TextWidget | None = None,
        on_confirm: OnClick | WidgetEventProcessor | None = None,
        on_cancel: OnClick | WidgetEventProcessor | None = None,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(id=id, when=when)
        self.primary_text = primary_text
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.are_you_sure_text = are_you_sure_text
        self.on_confirm = ensure_event_processor(on_confirm)
        self.on_cancel = ensure_event_processor(on_cancel)

    async def _process_item_callback(
        self,
        callback: MessageCallback,
        data: str,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        if data == "__confirm__":
            await self.on_confirm.process_event(callback, self, manager)
        elif data == "__cancel__":
            await self.on_cancel.process_event(callback, self, manager)
        return True

    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        payload: str | None = manager.middleware_data.get("aiogd_original_payload")
        action = self._get_action(payload)

        # Если кнопка с primary_text
        if action == "__wait__":
            return [
                [
                    CallbackButton(
                        text=await self.are_you_sure_text.render_text(data, manager),
                        payload=f"{self.callback_prefix()}__wait__",
                    ),
                ],
                [
                    CallbackButton(
                        text=await self.cancel_text.render_text(data, manager),
                        payload=f"{self.callback_prefix()}__cancel__",
                    ),
                    CallbackButton(
                        text=await self.confirm_text.render_text(data, manager),
                        payload=f"{self.callback_prefix()}__confirm__",
                    ),
                ],
            ]

        # Любая другая кнопка, из другого окна или cancel/confirm
        return [
            [
                CallbackButton(
                    text=await self.primary_text.render_text(data, manager),
                    payload=f"{self.callback_prefix()}__wait__",
                ),
            ],
        ]

    def _get_action(self, payload: str | None) -> str | None:
        if payload is None:
            return None

        # убрать intent, потому что в _render_keyboard попадает что угодно
        _, payload = remove_intent_id(payload)

        # проверка что кнопка относится к этому виджету
        prefix = self.callback_prefix()
        if not prefix or not payload.startswith(prefix):
            return None

        # ищем action (__confirm__ итп)
        parts = payload.split(":", 1)
        return parts[1] if len(parts) > 1 else None
