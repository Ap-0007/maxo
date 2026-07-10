from abc import abstractmethod
from collections.abc import Callable
from typing import Any

from maxo.dialogs.api.entities import ChatEvent
from maxo.dialogs.api.protocols import DialogManager


class WidgetEventProcessor:
    @abstractmethod
    async def process_event(
        self,
        event: ChatEvent,
        source: Any,
        manager: DialogManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        raise NotImplementedError

    def __bool__(self) -> bool:
        return True


class SimpleEventProcessor(WidgetEventProcessor):
    def __init__(self, callback: Callable[..., Any] | None) -> None:
        self.callback = callback

    async def process_event(
        self,
        event: ChatEvent,
        source: Any,
        manager: DialogManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if self.callback is not None:
            await self.callback(event, source, manager, *args, **kwargs)

    def __bool__(self) -> bool:
        return self.callback is not None


def ensure_event_processor(
    processor: Callable[..., Any] | WidgetEventProcessor | None,
) -> WidgetEventProcessor:
    if isinstance(processor, WidgetEventProcessor):
        return processor
    return SimpleEventProcessor(processor)
