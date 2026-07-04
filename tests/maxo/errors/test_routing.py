from typing import cast
from unittest.mock import MagicMock

from maxo.errors.routing import CycleRoutersError
from maxo.routing.interfaces import BaseRouter


class NamedRouter:
    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name


def router(name: str) -> BaseRouter:
    # cast нужен: CycleRoutersError в этих тестах использует только str(router).
    return cast(BaseRouter, NamedRouter(name))


def test_cycle_routers_error_single_router() -> None:
    mock_router = router("Router1")

    error = CycleRoutersError([mock_router])

    result = str(error)
    assert "Cycle routers detected" in result
    assert "⥁ Router1" in result


def test_cycle_routers_error_multiple_routers() -> None:
    router1 = router("Router1")
    router2 = router("Router2")
    router3 = router("Router3")

    error = CycleRoutersError([router1, router2, router3])

    result = str(error)
    assert "Cycle routers detected" in result
    assert "╭─>─╮" in result
    assert "Router1" in result
    assert "Router2" in result
    assert "Router3" in result
    assert "│   ▼" in result
    assert "╰─<─╯" in result


def test_cycle_routers_error_has_routers_attribute() -> None:
    routers = [MagicMock(), MagicMock()]
    error = CycleRoutersError(routers)

    assert error.routers == routers
