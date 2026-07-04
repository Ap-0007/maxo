from unittest.mock import MagicMock

from maxo.errors.routing import CycleRoutersError


def test_cycle_routers_error_single_router() -> None:
    mock_router = MagicMock()
    mock_router.__str__ = lambda _: "Router1"

    error = CycleRoutersError([mock_router])

    result = str(error)
    assert "Cycle routers detected" in result
    assert "⥁ Router1" in result


def test_cycle_routers_error_multiple_routers() -> None:
    router1 = MagicMock()
    router1.__str__ = lambda _: "Router1"
    router2 = MagicMock()
    router2.__str__ = lambda _: "Router2"
    router3 = MagicMock()
    router3.__str__ = lambda _: "Router3"

    error = CycleRoutersError([router1, router2, router3])

    result = str(error)
    assert "Cycle routers detected" in result
    assert "╭─>─╮" in result
    assert "Router1" in result
    assert "Router2" in result
    assert "Router3" in result
    assert "│   ▼" in result
    assert "╰─<─╯" in result


def test_cycle_routers_error_render_details_single() -> None:
    mock_router = MagicMock()
    mock_router.__str__ = lambda _: "SingleRouter"

    error = CycleRoutersError([mock_router])
    details = error._render_details()

    assert details == "⥁ SingleRouter"


def test_cycle_routers_error_render_details_multiple() -> None:
    router1 = MagicMock()
    router1.__str__ = lambda _: "R1"
    router2 = MagicMock()
    router2.__str__ = lambda _: "R2"

    error = CycleRoutersError([router1, router2])
    details = error._render_details()

    assert "╭─>─╮" in details
    assert "│ R1" in details
    assert "│   ▼" in details
    assert "│ R2" in details
    assert "╰─<─╯" in details


def test_cycle_routers_error_has_routers_attribute() -> None:
    routers = [MagicMock(), MagicMock()]
    error = CycleRoutersError(routers)

    assert error.routers == routers
