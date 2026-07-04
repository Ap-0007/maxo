from dataclasses import dataclass

from maxo.dialogs import DialogManager
from maxo.dialogs.api.internal import RawKeyboard
from maxo.dialogs.widgets.common import WhenCondition
from maxo.dialogs.widgets.kbd import Keyboard


@dataclass
class KeyboardButton:
    text: str


class Button(Keyboard):
    def __init__(self, id: str, when: WhenCondition = None):
        super().__init__(when=when, id=id)

    async def _render_keyboard(
        self,
        data,
        manager: DialogManager,
    ) -> RawKeyboard:
        return [[KeyboardButton(text=self.widget_id)]]


async def test_or(mock_manager: DialogManager) -> None:
    text = Button("a") | Button("b")
    res = await text.render_keyboard({}, mock_manager)
    assert res == [[KeyboardButton(text="a")]]


async def test_or_condition(mock_manager: DialogManager) -> None:
    text = (
        Button("A", when=lambda data, widget, manager: bool(data.get("a")))
        | Button("B", when=lambda data, widget, manager: bool(data.get("b")))
        | Button("C")
    )
    res = await text.render_keyboard({"a": True}, mock_manager)
    assert res == [[KeyboardButton(text="A")]]
    res = await text.render_keyboard({"b": True}, mock_manager)
    assert res == [[KeyboardButton(text="B")]]
    res = await text.render_keyboard({}, mock_manager)
    assert res == [[KeyboardButton(text="C")]]
