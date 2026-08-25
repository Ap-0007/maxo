from abc import abstractmethod
from typing import Any, Protocol

from maxo.dialogs.api.entities import Data, MessageEvent, NewMessage
from maxo.dialogs.api.protocols import DialogManager, DialogProtocol
from maxo.fsm import State
from maxo.types import MessageCallback

from .widgets import Widget


class WindowProtocol(Protocol):
    @abstractmethod
    async def process_message(
        self,
        message: MessageEvent,
        dialog: "DialogProtocol",
        manager: DialogManager,
    ) -> bool:
        """Return True if message in handled."""
        raise NotImplementedError

    @abstractmethod
    async def process_callback(
        self,
        callback: MessageCallback,
        dialog: "DialogProtocol",
        manager: DialogManager,
    ) -> bool:
        """Return True if callback in handled."""
        raise NotImplementedError

    @abstractmethod
    async def process_result(
        self,
        start_data: Data,
        result: Any,
        manager: "DialogManager",
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def render(
        self,
        dialog: "DialogProtocol",
        manager: DialogManager,
    ) -> NewMessage:
        raise NotImplementedError

    @abstractmethod
    def get_state(self) -> State:
        raise NotImplementedError

    @abstractmethod
    def find(self, widget_id: str) -> Widget | None:
        raise NotImplementedError
