import importlib
import sys
from types import ModuleType
from typing import Any, ClassVar, Self, cast

import pytest

from maxo import Dispatcher
from maxo.dialogs import Dialog, Window
from maxo.dialogs.widgets.kbd import Back, Cancel, Group, Next, Start
from maxo.dialogs.widgets.text import Const
from maxo.fsm import State, StatesGroup


class MainSG(StatesGroup):
    start = State()
    next = State()


class ChildSG(StatesGroup):
    start = State()


class FakeContext:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class FakeNode:
    edges: ClassVar[list[tuple["FakeNode", "FakeNode"]]] = []

    def __init__(self, label: str, icon_path: str) -> None:
        self.label = label
        self.icon_path = icon_path

    def __rshift__(self, edge: object) -> "FakeConnector":
        return FakeConnector(self, edge)


class FakeConnector:
    def __init__(self, from_node: FakeNode, edge: object) -> None:
        self.from_node = from_node
        self.edge = edge

    def __rshift__(self, to_node: FakeNode) -> FakeNode:
        FakeNode.edges.append((self.from_node, to_node))
        return to_node


class FakeEdge:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


def install_fake_diagrams(monkeypatch: pytest.MonkeyPatch) -> None:
    diagrams = ModuleType("diagrams")
    diagrams_module = cast(Any, diagrams)
    diagrams_module.Node = FakeNode
    diagrams_module.Edge = FakeEdge
    diagrams_module.Cluster = FakeContext
    diagrams_module.Diagram = FakeContext

    custom = ModuleType("diagrams.custom")
    custom_module = cast(Any, custom)
    custom_module.Custom = FakeNode

    monkeypatch.setitem(sys.modules, "diagrams", diagrams)
    monkeypatch.setitem(sys.modules, "diagrams.custom", custom)
    sys.modules.pop("maxo.dialogs.tools.transitions", None)


def test_render_transitions_with_fake_diagrams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeNode.edges.clear()
    install_fake_diagrams(monkeypatch)
    transitions = importlib.import_module("maxo.dialogs.tools.transitions")
    dp = Dispatcher()
    dp.include(
        Dialog(
            Window(
                Const("First"),
                Group(
                    Next(),
                    Start(Const("Start"), id="start", state=ChildSG.start),
                    Cancel(),
                    id="group",
                ),
                state=MainSG.start,
            ),
            Window(Const("Second"), Back(), state=MainSG.next),
        ),
    )
    dp.include(Dialog(Window(Const("Child"), Cancel(), state=ChildSG.start)))

    transitions.render_transitions(dp)

    assert FakeNode.edges


def test_render_transitions_reports_missing_optional_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_diagrams(monkeypatch)
    transitions = importlib.import_module("maxo.dialogs.tools.transitions")
    original_import_module = importlib.import_module

    def raise_import_error(name: str) -> ModuleType:
        if name == "diagrams":
            raise ImportError("missing diagrams")
        return original_import_module(name)

    monkeypatch.setattr(transitions.importlib, "import_module", raise_import_error)

    with pytest.raises(ImportError, match="Install maxo\\[preview\\]"):
        transitions.render_transitions(Dispatcher())
