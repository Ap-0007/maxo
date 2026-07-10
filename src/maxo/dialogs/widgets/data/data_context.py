from typing import Any

from maxo.dialogs.api.internal.widgets import DataGetter
from maxo.dialogs.api.protocols import DialogManager


class CompositeGetter:
    def __init__(self, *getters: DataGetter) -> None:
        self.getters: list[DataGetter] = list(getters)

    async def __call__(self, **kwargs: Any) -> dict[Any, Any]:
        data: dict[Any, Any] = {}
        for g in self.getters:
            data.update(await g(**kwargs))
        return data


class StaticGetter:
    def __init__(self, data: dict[Any, Any]) -> None:
        self.data = data

    async def __call__(self, **kwargs: Any) -> dict[Any, Any]:
        return self.data


class PreviewAwareGetter:
    def __init__(self, normal_getter: DataGetter, preview_getter: DataGetter) -> None:
        self.normal_getter = normal_getter
        self.preview_getter = preview_getter

    async def __call__(
        self,
        dialog_manager: DialogManager,
        **kwargs: Any,
    ) -> dict[Any, Any]:
        if dialog_manager.is_preview():
            return await self.preview_getter(
                dialog_manager=dialog_manager,
                **kwargs,
            )
        return await self.normal_getter(
            dialog_manager=dialog_manager,
            **kwargs,
        )
