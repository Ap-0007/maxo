import maxo
from maxo import bot as bot_package, methods
from maxo.__meta__ import __version__
from maxo.bot.bot import Bot
from maxo.bot.methods import SendMessage
from maxo.routing.ctx import Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.interfaces.middleware import BaseMiddleware
from maxo.routing.routers.simple import Router
from maxo.types import MessageCreated
from maxo.utils.text_decorations import html_decoration, markdown_decoration


def test_top_level_exports() -> None:
    assert maxo.Bot is Bot
    assert maxo.Dispatcher is Dispatcher
    assert maxo.Router is Router
    assert maxo.Ctx is Ctx
    assert maxo.BaseMiddleware is BaseMiddleware
    assert maxo.__version__ == __version__


def test_top_level_text_decorations() -> None:
    assert maxo.html is html_decoration
    assert maxo.md is markdown_decoration


def test_top_level_modules() -> None:
    assert maxo.types.MessageCreated is MessageCreated
    assert maxo.methods.SendMessage is SendMessage
    assert maxo.enums.ChatType.DIALOG.value == "dialog"


def test_methods_module_mirrors_bot_methods() -> None:
    assert set(methods.__all__) == set(bot_package.methods.__all__)
    for name in methods.__all__:
        assert getattr(methods, name) is getattr(bot_package.methods, name)


def test_all_is_sorted_and_complete() -> None:
    assert list(maxo.__all__) == sorted(maxo.__all__)
    for name in maxo.__all__:
        assert hasattr(maxo, name), name
