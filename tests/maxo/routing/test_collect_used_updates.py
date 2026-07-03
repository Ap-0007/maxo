from maxo import Router
from maxo.enums import UpdateType
from maxo.routing.ctx import Ctx
from maxo.routing.filters import BaseFilter
from maxo.routing.updates import MessageCallback, MessageCreated
from maxo.routing.utils.collect_used_updates import collect_used_updates


async def message_handler(_: MessageCreated) -> None:
    return None


async def callback_handler(_: MessageCallback) -> None:
    return None


class TrueFilter(BaseFilter[MessageCreated]):
    async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
        return True


def test_collect_used_updates_empty_router() -> None:
    assert collect_used_updates(Router()) == ()


def test_collect_used_updates_from_router_tree() -> None:
    root = Router("root")
    child = Router("child")
    grandchild = Router("grandchild")
    root.include(child)
    child.include(grandchild)

    root.message_created.handler(message_handler)
    grandchild.message_callback.handler(callback_handler)

    assert set(collect_used_updates(root)) == {
        UpdateType.MESSAGE_CREATED,
        UpdateType.MESSAGE_CALLBACK,
    }


def test_collect_used_updates_ignores_alias_without_handlers() -> None:
    root = Router("root")
    child = Router("child")
    root.include(child)

    child.message_created.filter(TrueFilter())

    assert collect_used_updates(root) == ()
