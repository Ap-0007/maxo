from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import Url
from maxo.dialogs.widgets.text import Const


async def test_render_url(mock_manager: DialogManager) -> None:
    url = Url(
        Const("Github"),
        Const("https://github.com/K1rL3s/maxo"),
    )

    keyboard = await url.render_keyboard(data={}, manager=mock_manager)

    assert keyboard[0][0].text == "Github"
    assert keyboard[0][0].url == "https://github.com/K1rL3s/maxo"
