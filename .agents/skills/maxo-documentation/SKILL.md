---
name: maxo-documentation
description: "Используй при изменении документации maxo: docs на Sphinx/RST, README, examples, changelog, русскоязычные инструкции и актуальность импортов для версии 0.7.0."
---

# Документация maxo

Вся документация проекта и инструкции для AI-агентов пишутся на русском языке.
Проект ориентирован на российских разработчиков ботов для российского
мессенджера MAX.

## Где писать

- `README.md` - короткий обзор, установка и быстрые примеры.
- `docs/index.rst` - главная страница и `toctree`.
- `docs/pages/getting-started.rst` - старт.
- `docs/pages/event-handling/` - routing, filters, middlewares, handlers, FSM,
  facades, errors, signals, transports.
- `docs/pages/dialogs/` - `maxo.dialogs`.
- `docs/pages/botapi/` - Bot API, updates, types, methods, enums.
- `docs/pages/utils/` - утилиты.
- `docs/pages/changelog.md` - changelog.
- `examples/` - runnable-примеры публичного API.

## Стиль

- Русский язык.
- Только короткое тире `-`.
- Не используй устаревшие импорты из старых PR.
- Показывай актуальный API `0.7.0`.
- Примеры должны импортировать из публичных модулей.
- Не используй `maxo._internal` в пользовательской документации.
- В README оставляй компактные примеры, подробности переноси в `docs/pages`.

## Актуальные паттерны примеров

Минимальный бот:

```python
from maxo import Bot, Dispatcher
from maxo.routing.updates import MessageCreated
from maxo.transport.long_polling import LongPolling

bot = Bot("TOKEN")
dp = Dispatcher()


@dp.message_created()
async def echo_handler(message: MessageCreated) -> None:
    await message.answer(message.text or "Текста нет")


LongPolling(dp).run(bot)
```

Клавиатуры строятся через `maxo.utils.builders.KeyboardBuilder`.
`magic_filter` показывай через `maxo.integrations.magic_filter.MagicFilter`.
Для webhook используй `SimpleEngine`, `AiohttpWebAdapter` или
`FastApiWebAdapter`, `StaticRouting`, `Security`, `StaticSecretToken`,
`collect_used_updates`.

## Sphinx

При добавлении страницы обновляй `docs/index.rst` и нужный `toctree`.

Локальная сборка:

```bash
uv run sphinx-build -b html docs docs/_build/html
```

Если меняешь изображения или preview assets, проверь ссылки из RST.

## Когда обновлять docs

Обновляй docs/examples при изменении:

- публичных импортов;
- методов `Bot`;
- update-моделей и facades;
- filters/middlewares/handlers;
- FSM и dialogs;
- webhook/long-polling;
- optional extras;
- поведения ошибок.
