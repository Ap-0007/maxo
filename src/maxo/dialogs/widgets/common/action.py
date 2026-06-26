import re
from typing import Any, Optional, TypeVar, cast

from maxo.dialogs.api.exceptions import InvalidWidgetIdError
from maxo.dialogs.api.protocols import DialogManager

from .base import BaseWidget

T = TypeVar("T")


ID_PATTERN = re.compile("^[a-zA-Z0-9_.]+$")


class Actionable(BaseWidget):
    def __init__(self, id: str | None = None) -> None:
        if id and not ID_PATTERN.match(id):
            raise InvalidWidgetIdError(f"Invalid widget id: {id}")
        self.widget_id = id

    def find(self, widget_id: str) -> Optional["Actionable"]:
        """Find nested widget or current one by id."""
        if self.widget_id is not None and self.widget_id == widget_id:
            return self
        return None

    def get_widget_data(
        self,
        manager: DialogManager,
        default: T,
    ) -> Any | T:
        """Get data for current widget id, setting default if needed."""
        assert self.widget_id is not None  # noqa: S101
        widget_data = cast(
            "dict[str, Any]",
            manager.current_context().widget_data,
        )
        return widget_data.setdefault(self.widget_id, default)

    def set_widget_data(
        self,
        manager: DialogManager,
        value: T,
    ) -> None:
        """Set data for current widget id."""
        assert self.widget_id is not None  # noqa: S101
        widget_data = cast(
            "dict[str, Any]",
            manager.current_context().widget_data,
        )
        widget_data[self.widget_id] = value

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.widget_id}>"
