---
name: maxo-bot-api
description: Используй при добавлении или изменении методов MAX Bot API, types, enums, updates, сериализации adaptix, Bot/MaxApiClient, unihttp-маркеров и generated API surface.
---

# Bot API maxo

Этот skill нужен для изменений в Bot API слое: `src/maxo/bot`,
`src/maxo/types`, `src/maxo/enums`, `src/maxo/routing/updates`,
`src/maxo/serialization.py`.

## Общий принцип

Не правь generated API surface как одиночный ручной фикс. Если меняется
контракт MAX Bot API, синхронизируй:

- метод в `src/maxo/bot/methods/...`;
- типы в `src/maxo/types/...`;
- enum в `src/maxo/enums/...`;
- update-модель в `src/maxo/routing/updates/...`;
- facade/mixin при пользовательском удобстве;
- `serialization.py` для polymorphic loading/dumping;
- тесты и docs.

## Методы Bot API

Метод - класс `MaxoMethod[Result]`:

```python
class SendMessage(MaxoMethod[SendMessageResult]):
    __url__ = "messages"
    __method__ = "post"

    chat_id: Query[Omittable[int]] = Omitted()
    text: Body[str | None] = None
```

Правила:

- Используй markers из `maxo.bot.methods.markers`.
- Path/query/header/body должны соответствовать wire-контракту API.
- Generic-параметр `MaxoMethod[Result]` - тип результата после deserialization.
- `Bot` привязывает методы через `bind_method`. Для обычного endpoint не пиши
  ручной passthrough.
- Если метод требует особого поведения ответа, делай это в методе или клиенте
  осознанно и покрывай тестом.

## `Omitted()` и `None`

- `Omitted()` - поле не отправляется.
- `None` - поле отправляется как `null`, если marker и API это допускают.
- Не заменяй одно другим без проверки документации MAX API и теста.

## Типы и enum

- API-модели наследуются от `MaxoType`.
- Docstrings и field docs - на русском.
- Для optional wire-полей используй `Omittable[T] = Omitted()`.
- Для поля, которое может прийти как `null`, используй `Omittable[T | None]`.
- Для unsafe-доступа к omitted/null полям следуй паттерну
  `unsafe_sender`, `unsafe_url` и `AttributeIsEmptyError`.

## Сериализация

`src/maxo/serialization.py` строит `Retort`:

- `TAG_PROVIDERS` связывает discriminators (`update_type`, `type`) с классами.
- Query dumper преобразует `None`, `bool`, списки.
- Defaults для `SendMessage`, `EditMessage`, `NewMessageBody` применяются через
  `BotDefaults`.
- Attachments request conversion идет через `to_request()`.
- Timestamp API грузится в `datetime` с `UTC`.
- `create_retort_with_bot` привязывает `Bot` ко всем `MaxoType`.

При добавлении нового polymorphic варианта обязательно обновляй
`TAG_PROVIDERS` и тесты загрузки.

## MaxApiClient

`MaxApiClient`:

- наследуется от `unihttp.clients.aiohttp.AiohttpAsyncClient`;
- по умолчанию использует `https://platform-api2.max.ru/`;
- добавляет российский trusted CA из `russiantrustedca.pem`;
- ставит `Authorization` и `User-Agent`;
- мапит HTTP-статусы на `MaxBotApiError` subclasses;
- превращает некоторые `success=false` ответы в ошибку, кроме особого случая
  `AddMembers`.

Не ломай эти гарантии без отдельного теста и обновления docs.

## Тесты

Покрывай:

- build request: query/body/path markers;
- dump defaults и `Omitted()`;
- load response и update polymorphism;
- error mapping;
- backward-compatible imports из `__init__.py`;
- user-facing shortcuts/facades, если они добавлены.
