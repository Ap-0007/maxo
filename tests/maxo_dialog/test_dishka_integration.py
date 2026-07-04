from unittest.mock import MagicMock

from dishka import FromDishka, Provider, Scope, make_async_container, provide

from maxo.dialogs.integrations.dishka import inject
from maxo.integrations.dishka import CONTAINER_NAME


class DialogService:
    def marker(self) -> str:
        return "dialog-service"


class DialogProvider(Provider):
    @provide(scope=Scope.APP)
    def service(self) -> DialogService:
        return DialogService()


async def test_dialog_dishka_inject_uses_container_from_kwargs() -> None:
    container = make_async_container(DialogProvider())

    @inject
    async def getter(
        service: FromDishka[DialogService],
        **kwargs: object,
    ) -> str:
        assert CONTAINER_NAME in kwargs
        return service.marker()

    try:
        assert await getter(**{CONTAINER_NAME: container}) == "dialog-service"
    finally:
        await container.close()


async def test_dialog_dishka_inject_uses_manager_for_dialog_event() -> None:
    container = make_async_container(DialogProvider())
    manager = MagicMock()
    manager.middleware_data = {CONTAINER_NAME: container}

    @inject
    async def on_dialog_event(
        data: dict[str, str],
        manager: object,
        service: FromDishka[DialogService],
    ) -> str:
        return f"{data['value']}:{service.marker()}"

    try:
        assert await on_dialog_event({"value": "data"}, manager) == (
            "data:dialog-service"
        )
    finally:
        await container.close()


async def test_dialog_dishka_inject_uses_manager_for_widget_event() -> None:
    container = make_async_container(DialogProvider())
    manager = MagicMock()
    manager.middleware_data = {CONTAINER_NAME: container}

    @inject
    async def on_widget_event(
        event: object,
        widget: object,
        manager: object,
        service: FromDishka[DialogService],
    ) -> str:
        return service.marker()

    try:
        assert await on_widget_event(object(), object(), manager) == "dialog-service"
    finally:
        await container.close()
