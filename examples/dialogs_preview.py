"""Демонстрация maxo.dialogs.tools: HTML-превью и диаграмма переходов.

Запуск (генерирует preview.html и maxo_dialog.png в текущей директории):
    python examples/dialogs_preview.py

Запуск web-сервера (http://127.0.0.1:9876/):
    maxo-dialog-preview examples/dialogs_preview:router

Требования для диаграммы переходов:
    pip install "maxo[preview]"
    brew install graphviz   # macOS
    apt-get install graphviz  # Linux
"""

import asyncio
from typing import Any

from maxo import Dispatcher
from maxo.dialogs import Dialog, DialogManager, StartMode, Window
from maxo.dialogs.widgets.kbd import Back, Button, Cancel, Start, SwitchTo
from maxo.dialogs.widgets.text import Const
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.routing.filters import CommandStart
from maxo.types import MessageCreated

# ---------------------------------------------------------------------------
# Состояния
# ---------------------------------------------------------------------------


class CatalogSG(StatesGroup):
    main = State()
    detail = State()


class SettingsSG(StatesGroup):
    main = State()


# ---------------------------------------------------------------------------
# Обработчики
# ---------------------------------------------------------------------------


async def on_start(
    message: MessageCreated,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.start(CatalogSG.main, mode=StartMode.RESET_STACK)


async def on_detail_click(
    callback: Any,
    button: Any,
    manager: DialogManager,
) -> None:
    await manager.switch_to(CatalogSG.detail)


# ---------------------------------------------------------------------------
# Диалоги
# ---------------------------------------------------------------------------


def make_catalog_dialog() -> Dialog:
    return Dialog(
        Window(
            Const("Каталог"),
            Button(Const("Подробнее"), id="detail", on_click=on_detail_click),
            Start(Const("Настройки"), id="settings", state=SettingsSG.main),
            state=CatalogSG.main,
        ),
        Window(
            Const("Детальная страница"),
            SwitchTo(Const("← Назад"), id="back", state=CatalogSG.main),
            state=CatalogSG.detail,
        ),
    )


def make_settings_dialog() -> Dialog:
    return Dialog(
        Window(
            Const("Настройки"),
            Back(),
            Cancel(),
            state=SettingsSG.main,
        ),
    )


# ---------------------------------------------------------------------------
# Роутер на уровне модуля - нужен для maxo-dialog-preview
# ---------------------------------------------------------------------------

router = Dispatcher(key_builder=DefaultKeyBuilder(with_destiny=True))
router.message_created.handler(on_start, CommandStart())
router.include(make_catalog_dialog())
router.include(make_settings_dialog())


# ---------------------------------------------------------------------------
# Точка входа - генерирует файлы напрямую
# ---------------------------------------------------------------------------


async def main() -> None:
    from maxo.dialogs.tools.preview import render_preview  # noqa: PLC0415
    from maxo.dialogs.tools.transitions import render_transitions  # noqa: PLC0415

    try:
        await render_preview(router, "preview.html")
        print("HTML-превью сохранено: preview.html")
    except Exception as e:  # noqa: BLE001
        print(f"HTML-превью недоступно: {e}")

    try:
        render_transitions(router, title="Пример бота", filename="maxo_dialog")
        print("Диаграмма переходов сохранена: maxo_dialog.png")
    except Exception as e:  # noqa: BLE001
        print(f"Диаграмма переходов недоступна: {e}")


if __name__ == "__main__":
    asyncio.run(main())
