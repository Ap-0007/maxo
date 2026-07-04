import sys
from types import ModuleType
from typing import Any, cast

import pytest

from maxo.dialogs.tools import web_preview
from maxo.dialogs.tools.web_preview import Renderer, removesuffix
from maxo.routing.interfaces import BaseRouter


class DummyRouter:
    pass


def install_module(monkeypatch: pytest.MonkeyPatch, name: str, value: Any) -> None:
    module = ModuleType(name)
    module.__dict__["dialogs_router"] = value
    monkeypatch.setitem(sys.modules, name, module)


def test_removesuffix() -> None:
    assert removesuffix("diagram.png", ".png") == "diagram"
    assert removesuffix("diagram.svg", ".png") == "diagram.svg"


async def test_renderer_get_router_from_object(monkeypatch: pytest.MonkeyPatch) -> None:
    router = cast(BaseRouter, DummyRouter())
    install_module(monkeypatch, "test_preview_object", router)

    assert (
        await Renderer("test_preview_object", "dialogs_router")._get_router() is router
    )


async def test_renderer_get_router_from_sync_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = cast(BaseRouter, DummyRouter())
    install_module(monkeypatch, "test_preview_sync", lambda: router)

    assert await Renderer("test_preview_sync", "dialogs_router")._get_router() is router


async def test_renderer_get_router_from_async_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = cast(BaseRouter, DummyRouter())

    async def factory() -> BaseRouter:
        return router

    install_module(monkeypatch, "test_preview_async", factory)

    assert (
        await Renderer("test_preview_async", "dialogs_router")._get_router() is router
    )


async def test_renderer_load_preview(monkeypatch: pytest.MonkeyPatch) -> None:
    router = cast(BaseRouter, DummyRouter())
    install_module(monkeypatch, "test_preview_load", router)

    async def render_preview_content(
        loaded_router: BaseRouter,
        simulate_events: bool,
    ) -> str:
        assert loaded_router is router
        assert simulate_events is True
        return "<html></html>"

    monkeypatch.setattr(web_preview, "render_preview_content", render_preview_content)

    assert await Renderer("test_preview_load", "dialogs_router")._load_preview() == (
        "<html></html>"
    )


async def test_renderer_load_transitions(monkeypatch: pytest.MonkeyPatch) -> None:
    router = cast(BaseRouter, DummyRouter())
    called: dict[str, Any] = {}
    install_module(monkeypatch, "test_preview_transitions", router)

    def render_transitions(loaded_router: BaseRouter, filename: str) -> None:
        called["router"] = loaded_router
        called["filename"] = filename

    monkeypatch.setattr(web_preview, "render_transitions", render_transitions)

    await Renderer("test_preview_transitions", "dialogs_router")._load_transitions(
        "diagram.png",
    )

    assert called == {"router": router, "filename": "diagram"}
