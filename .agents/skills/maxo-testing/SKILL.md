---
name: maxo-testing
description: "Используй при написании или изменении тестов maxo: pytest, pytest-asyncio, routing, Bot API, webhook, dialogs, test tools, coverage и точечные команды."
---

# Тестирование maxo

## Запуск

```bash
uv run pytest tests/ --cov=src --cov-report=term
uv run pytest tests/path/test_file.py::test_name -v
```

Полная матрица Python:

```bash
uv run nox -s test
```

## Общие правила

- `pytest-asyncio` работает в `auto` mode.
- Async-поведение тестируй async-тестами, не создавай event loop вручную.
- Не добавляй тесты, которые требуют реального MAX API или сетевого доступа.
- Используй `unittest.mock.AsyncMock` и `MagicMock`.
- В тестах допускаются `assert`, длинные строки и отсутствие docstrings, но
  `mypy` все равно проверяет `tests`, поэтому аннотации и типовая корректность
  важны.
- Тест должен фиксировать поведение, а не внутреннюю реализацию, если только
  задача не касается внутреннего контракта.

## Раскладка

- `tests/maxo/` - ядро, routing, bot, transport, integrations, utils.
- `tests/maxo_dialog/` - диалоговая система.
- `tests/maxo_webhook/` - webhook engines, adapters, routing, security.
- `tests/maxo_dialog/widgets/` - widgets по типам.

## Routing и FSM

- Для handler/filter/middleware тестов используй существующие фикстуры рядом с
  подсистемой.
- Проверяй порядок обработки, если меняешь `Router.include`, observers,
  middleware или `UNHANDLED`/`SkipHandler` поведение.
- Для FSM проверяй state, data, key builder и event isolation там, где меняется
  контракт хранения.

## Dialogs

Для `maxo.dialogs` предпочитай инструменты из
`src/maxo/dialogs/test_tools`:

- `BotClient`
- `MockMessageManager`
- memory storage
- keyboard helpers/locators

Проверяй:

- старт и закрытие диалога;
- переходы между окнами;
- callback widgets;
- сохранение dialog data;
- фоновые менеджеры, если они затронуты;
- уникальность и стабильность widget `id`.

## Bot API и сериализация

При изменении методов, типов, enum или `serialization.py` добавляй тесты на:

- dump request body/query/path через `unihttp` markers;
- load response/update в правильную модель;
- `Omitted()` против `None`;
- polymorphic dispatch по `type` или `update_type`;
- ошибки API, если меняется `MaxApiClient.handle_error`.

## Webhook

- Используй fixtures из `tests/maxo_webhook`.
- Тестируй adapters (`aiohttp`, `fastapi`) без реального внешнего сервиса.
- Security checks должны покрывать положительный и отрицательный сценарии.

## Что запускать перед финалом

Минимум - релевантный точечный `pytest`. Для широких изменений - весь
`uv run pytest tests/ --cov=src --cov-report=term`, затем ruff и mypy.
