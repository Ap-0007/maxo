from maxo.__meta__ import __version__
from maxo.bot.bot import Bot
from maxo.routing.ctx import Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.interfaces.middleware import BaseMiddleware
from maxo.routing.routers.simple import Router
from maxo.utils.text_decorations import (
    html_decoration as html,
    markdown_decoration as md,
)

# Импортируются после `Bot`: `maxo.routing` и `maxo.bot` делают `from maxo import Bot`,
# поэтому имя `Bot` должно попасть в неймспейс пакета раньше.
from maxo import enums, methods, types  # isort: skip

__all__ = (
    "BaseMiddleware",
    "Bot",
    "Ctx",
    "Dispatcher",
    "Router",
    "__version__",
    "enums",
    "html",
    "md",
    "methods",
    "types",
)
