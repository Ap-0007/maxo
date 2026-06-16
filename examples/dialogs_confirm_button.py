import asyncio
import logging
import os

from maxo import Bot, Dispatcher, Router
from maxo.dialogs import (
    Dialog,
    DialogManager,
    ShowMode,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.widgets.kbd import ConfirmButton
from maxo.dialogs.widgets.text import Const
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.memory import MemoryStorage, SimpleEventIsolation
from maxo.routing.updates import MessageCallback, MessageCreated
from maxo.transport.long_polling import LongPolling


class SG(StatesGroup):
    main = State()


async def on_confirm_handler(
    callback: MessageCallback,
    widget: ConfirmButton,
    manager: DialogManager,
) -> None:
    await callback.message.answer("Action confirmed!")
    manager.show_mode = ShowMode.SEND


async def on_cancel_handler(
    callback: MessageCallback,
    widget: ConfirmButton,
    manager: DialogManager,
) -> None:
    await callback.message.answer("Action canceled!")
    manager.show_mode = ShowMode.SEND


confirm_dialog = Dialog(
    Window(
        Const("Click at any button to see the confirmation flow"),
        ConfirmButton(
            primary_text=Const("Primary 1"),
            confirm_text=Const("Confirm 1"),
            cancel_text=Const("Cancel 1"),
            are_you_sure_text=Const("Are you sure? 1"),
            id="1",
            on_confirm=on_confirm_handler,
            on_cancel=on_cancel_handler,
        ),
        ConfirmButton(
            primary_text=Const("Primary 2"),
            confirm_text=Const("Confirm 2"),
            cancel_text=Const("Cancel 2"),
            are_you_sure_text=Const("Are you sure? 2"),
            id="2",
            on_confirm=on_confirm_handler,
            on_cancel=on_cancel_handler,
        ),
        state=SG.main,
    ),
)

router = Router()


@router.message_created()
async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(
        state=SG.main,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
    )


async def main() -> None:
    bot = Bot(os.environ["TOKEN"])

    key_builder = DefaultKeyBuilder(with_destiny=True)
    events_isolation = SimpleEventIsolation(key_builder=key_builder)
    dp = Dispatcher(
        storage=MemoryStorage(key_builder=key_builder),
        events_isolation=events_isolation,
        key_builder=key_builder,
    )

    dp.include(router, confirm_dialog)
    setup_dialogs(dp)

    await LongPolling(dp).start(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
