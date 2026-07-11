# ruff: noqa: PLC0415
import importlib

import pytest

from maxo import types


def test_deprecation_warning() -> None:
    import maxo.routing.updates

    with pytest.warns(
        DeprecationWarning,
        match="Апдейты были перенесены из `maxo.routing.updates` в `maxo.types`",
    ):
        importlib.reload(maxo.routing.updates)


def test_all_updates_are_reexported_from_types() -> None:
    import maxo.routing.updates as updates

    for name in updates.__all__:
        assert hasattr(updates, name)
        assert getattr(updates, name) is getattr(types, name)
