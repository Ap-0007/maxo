---
name: maxo-architecture
description: "Используй при изменении исходного кода maxo в src/maxo: архитектура пакета, публичный API, Bot, routing, FSM, dialogs, transport, integrations, сериализация и правила совместимости."
---

# Архитектура maxo

`maxo` - асинхронный Python-фреймворк для ботов MAX. Текущая версия проекта -
`0.7.0`, Python - `>=3.12,<3.15`.

## Карта пакета

- `bot/` - `Bot`, `MaxApiClient`, состояния бота, методы Bot API.
- `types/` и `enums/` - модели MAX Bot API. Значительная часть файлов
  сгенерирована по документации API.
- `routing/` - `Dispatcher`, `Router`, observers, handlers, filters,
  middlewares, facades, updates, signals.
- `fsm/` - `State`, `StatesGroup`, `FSMContext`, storage, isolation,
  key builders.
- `dialogs/` - диалоговая система поверх FSM, порт из `aiogram_dialog`.
- `transport/` - long polling и webhook.
- `integrations/` - `dishka`, `magic_filter`.
- `utils/` - builders, upload helpers, formatting, links, facades.
- `_internal/` - внутренние helpers. Не используй их в docs и examples.

## Публичный API

- Top-level `maxo` экспортирует только `Bot`, `Dispatcher`, `Router`, `Ctx`,
  `BaseMiddleware`.
- При добавлении публичного символа обновляй ближайший `__init__.py` и
  `__all__`, если модуль использует явный экспорт.
- Документация и примеры должны импортировать из публичных модулей, а не из
  `maxo._internal`.
- Не расширяй top-level `maxo` без причины: туда попадают только самые частые
  объекты, нужные почти каждому боту.

## Стиль кода

- Весь пользовательский текст и docstrings публичного API - на русском.
- Используй только короткое тире `-`.
- Двойные кавычки, 4 пробела, 88 символов.
- Строгая типизация: `mypy strict`.
- Для API-моделей наследуйся от `MaxoType`. Для внутренних dataclass следуй
  локальному стилю и предпочитай `slots=True`.
- Не добавляй side effects в конструкторы, если соседний код не требует этого.
- Не делай function-level imports без явной причины.

## Routing

Поток обработки:

```text
LongPolling/Webhook -> Dispatcher -> Router tree
outer middleware -> filters -> inner middleware -> handler
```

- `Dispatcher` - корневой `Router`, добавляющий workflow data, error/update
  middleware, FSM middleware и facade middleware.
- `Router.include(...)` задает приоритет. Первый обработавший обычный update
  останавливает дальнейший поиск.
- `message`, `callback_query`, `edited_message` - aiogram-подобные алиасы.
  В новых docs чаще используй явные `message_created`, `message_callback`.
- Update-модели и facades получают `bot` через middleware/serialization. Не
  ломай вызовы вида `await message.answer(...)`.

## FSM и dialogs

- FSM включена в `Dispatcher` по умолчанию.
- Default storage/isolation - `MemoryStorage` и `SimpleEventIsolation`.
- Для production и нескольких процессов нужны Redis storage/isolation.
- `setup_dialogs(dp)` подключает dialog observers и middlewares к
  `Dispatcher`. Вызывай его после `dp.include(dialog_or_router)`.
- Для dialogs критична destiny-часть ключа. При кастомных key builders проверяй
  совместимость с `DefaultKeyBuilder(with_destiny=True)`.
- Widget `id` должен быть стабильным и уникальным в своем контексте.

## Transport

- Long polling живет в `maxo.transport.long_polling`.
- Webhook живет в `maxo.transport.webhook`: engines, adapters для `aiohttp` и
  `fastapi`, routing, security.
- Для webhook используй `collect_used_updates(dispatcher)`, чтобы подписывать
  только реально используемые update types.

## Когда менять документацию

Любое изменение публичного API, поведения routing/FSM/dialogs/transport или
пользовательских исключений требует обновления docs/examples и тестов.
