import importlib
import sys
from types import ModuleType

import pytest

from maxo.errors import MaxoError
from maxo.routing.filters import BaseFilter


def import_deprecated_module(name: str) -> ModuleType:
    sys.modules.pop(name, None)
    with pytest.warns(FutureWarning):
        return importlib.import_module(name)


def test_exceptions_alias_exports_errors() -> None:
    module = import_deprecated_module("maxo.exceptions")

    assert module.MaxoError is MaxoError
    assert "MaxoError" in module.__all__


def test_filters_alias_exports_routing_filters() -> None:
    module = import_deprecated_module("maxo.filters")

    assert module.BaseFilter is BaseFilter
    assert "BaseFilter" in module.__all__
