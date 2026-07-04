from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import WebApp
from maxo.dialogs.widgets.text import Const
from maxo.omit import Omitted
from maxo.types import OpenAppButton


async def test_render_web_app_without_payload(mock_manager: DialogManager) -> None:
    web_app = WebApp(
        Const("Open"),
        Const("my_app"),
    )

    keyboard = await web_app.render_keyboard(data={}, manager=mock_manager)

    button = keyboard[0][0]
    assert isinstance(button, OpenAppButton)
    assert button.text == "Open"
    assert button.web_app == "my_app"
    assert button.payload == Omitted()
    assert button.contact_id == Omitted()


async def test_render_web_app_with_payload(mock_manager: DialogManager) -> None:
    web_app = WebApp(
        Const("Open"),
        Const("my_app"),
        payload=Const("some_payload"),
    )

    keyboard = await web_app.render_keyboard(data={}, manager=mock_manager)

    button = keyboard[0][0]
    assert isinstance(button, OpenAppButton)
    assert button.payload == "some_payload"


async def test_render_web_app_with_contact_id(mock_manager: DialogManager) -> None:
    web_app = WebApp(
        Const("Open"),
        Const("my_app"),
        contact_id=42,
    )

    keyboard = await web_app.render_keyboard(data={}, manager=mock_manager)

    button = keyboard[0][0]
    assert isinstance(button, OpenAppButton)
    assert button.contact_id == 42
    assert button.payload == Omitted()
