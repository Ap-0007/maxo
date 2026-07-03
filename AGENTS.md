# AGENTS.md - правила разработки maxo для AI-агентов

Этот файл является единым источником правды для AI-агентов, работающих с
репозиторием `maxo`. Все инструкции, комментарии к разработке и
пользовательская документация для агентов в этом проекте пишутся на русском
языке.

`maxo` - асинхронный Python-фреймворк для разработки ботов российского
мессенджера MAX (`https://max.ru`). Текущая версия проекта: `0.7.0`.
Поддерживаемые версии Python: `3.12`, `3.13`, `3.14`.

## Единый источник инструкций

`AGENTS.md` - базовый и обязательный источник правил для всех AI-агентов.
`CLAUDE.md` должен оставаться симлинком на `./AGENTS.md`.

Не выноси обязательные правила в Claude-only skills или другие инструменты,
которые не читают Codex, Cursor, Copilot, Gemini и похожие агенты. Если
инструкции разрастутся, добавляй вложенные `AGENTS.md` ближе к области
ответственности, например `src/maxo/bot/AGENTS.md`, `tests/AGENTS.md` или
`docs/AGENTS.md`.

Специфичные файлы для отдельных инструментов допустимы только как тонкий слой
поверх `AGENTS.md`. В них нельзя держать единственную копию знаний о проекте.

## Рабочие команды

В текущем дереве есть `justfile`, поэтому полагайся на `just`, Используй команды через `just` или прямые команды через `uv`:

```bash
uv sync --all-groups
uv run ruff check --no-fix .
uv run mypy --config-file pyproject.toml
uv run pytest tests/ --cov=src --cov-report=term
uv run nox -s test
```

Для точечного запуска:

```bash
uv run pytest tests/path/test_file.py::test_name -v
uv run ruff check --no-fix src/maxo/path.py tests/path/test_file.py
```

Полезно помнить:

- `pyproject.toml` задает `ruff` c `fix = true`, поэтому для проверки без
  изменений используй `--no-fix`.
- `pytest` в проекте работает с `asyncio_mode = auto`.
- CI проверяет lint на Python `3.14` и тесты на Python `3.12`, `3.13`, `3.14`
  с разрешением зависимостей `lowest-direct` и `highest`.

## Архитектура проекта

Ключевые директории:

| Путь                     | Назначение                                                                                              |
|--------------------------|---------------------------------------------------------------------------------------------------------|
| `src/maxo/bot/`          | `Bot`, `MaxApiClient`, состояния бота, declarative Bot API methods на `unihttp`.                        |
| `src/maxo/types/`        | Типы MAX Bot API. Многие файлы сгенерированы по документации API.                                       |
| `src/maxo/enums/`        | Enum MAX Bot API. Многие файлы сгенерированы по документации API.                                       |
| `src/maxo/routing/`      | `Dispatcher`, `Router`, observers, handlers, filters, middlewares, facades, updates, signals.           |
| `src/maxo/fsm/`          | FSM: `State`, `StatesGroup`, `FSMContext`, storage, isolation, key builders.                            |
| `src/maxo/dialogs/`      | Диалоги, портированные из `aiogram_dialog`: `Dialog`, `Window`, widgets, managers, preview, test tools. |
| `src/maxo/transport/`    | Long polling и webhook engine/adapters/routing/security.                                                |
| `src/maxo/integrations/` | Интеграции `dishka` и `magic_filter`.                                                                   |
| `src/maxo/utils/`        | Builders, upload helpers, formatting, deeplink/link helpers, facades.                                   |
| `docs/`                  | Sphinx-документация на русском языке.                                                                   |
| `examples/`              | Рабочие примеры использования публичного API.                                                           |
| `tests/`                 | Pytest-тесты по подсистемам.                                                                            |

Общая модель системы:

```text
Long polling / webhook
  -> Dispatcher
  -> Router tree
  -> outer middleware
  -> filters
  -> inner middleware
  -> handler
```

Ключевые паттерны:

- `Dispatcher` - корневой `Router`.
- `Router.include(...)` задает порядок обхода дочерних роутеров.
- Первый обработавший обычный update останавливает дальнейший поиск.
- Сигналы `before_startup`, `after_startup`, `before_shutdown`,
  `after_shutdown` обрабатываются как lifecycle hooks, а не как обычные update.
- `message`, `callback_query`, `edited_message` - алиасы для совместимости с
  привычками из aiogram.
- Facade и update-модели умеют отвечать через mixins после привязки бота.
- Для webhook используй `collect_used_updates(dispatcher)`, чтобы подписывать
  только реально используемые update types.

## Публичный API

- Top-level `maxo` экспортирует только самые частые объекты:
  `Bot`, `Dispatcher`, `Router`, `Ctx`, `BaseMiddleware`.
- Не расширяй top-level `maxo` без причины. Менее частые объекты должны
  импортироваться из своих публичных модулей.
- Документация и примеры должны импортировать из публичных модулей, а не из
  `maxo._internal`.
- При добавлении публичного символа обновляй ближайший `__init__.py` и
  `__all__`, если модуль использует явный публичный экспорт.

## Главные правила разработки

- Пиши инструкции для ИИ, docstrings публичного API и пользовательскую
  документацию на русском языке.
- Используй только короткое тире `-`. Не добавляй другие Unicode-варианты тире.
- Не добавляй `Co-Authored-By` в коммиты и текст PR.
- Коммиты оформляй в стиле conventional commits, например `feat:`, `fix:`,
  `docs:`, `chore:`. Русский текст в сообщении допустим.
- Строки держи до 88 символов, используй двойные кавычки и отступ 4 пробела.
- Строгая типизация обязательна: `mypy` работает в `strict = true` для
  `src/maxo`, `tests` и `examples`.
- Публичный код должен быть полностью аннотирован. В тестах аннотации тоже
  проверяются `mypy`, хотя ruff-правила `ANN` для тестов отключены.
- Для внутренних путей используй `pathlib.Path`, если работа идет с файлами.
- Не добавляй top-level side effects, кроме декларативной регистрации,
  ожидаемой текущими API.
- Не прячь импорты внутрь функций без необходимости. Предпочитай обычные
  импорты на уровне модуля.
- Для новых data-моделей используй существующий стиль: `MaxoType` для
  API-моделей, `@dataclass(slots=True)` там, где в подсистеме уже принят
  dataclass-подход.
- Не редактируй сгенерированные типы, enum и методы Bot API вручную как
  изолированную правку. Если меняется контракт API, синхронизируй методы,
  типы, сериализацию, тесты и документацию.

## FSM и dialogs

- FSM включена в `Dispatcher` по умолчанию. Без явных настроек используются
  `MemoryStorage`, `SimpleEventIsolation`, `DefaultKeyBuilder`.
- Для production и нескольких процессов используй Redis storage/isolation и
  продуманную стратегию ключей.
- `maxo.dialogs` живет поверх FSM и добавляет свои observers/middlewares через
  `setup_dialogs(dp)`.
- `setup_dialogs` должен применяться к `Dispatcher` после подключения диалогов
  к роутеру.
- Для dialogs нужна изоляция с `DefaultKeyBuilder(with_destiny=True)`. В
  `setup_dialogs` это используется по умолчанию для dialog event isolation, но
  при кастомной FSM-конфигурации проверяй совместимость ключей.
- Все widget `id` внутри одного окна/диалога должны быть стабильными и
  уникальными.

## Bot API, `unihttp`, `adaptix`

- Методы Bot API - классы `MaxoMethod[Result]` с `__url__`, `__method__` и
  marker-полями из `maxo.bot.methods.markers`.
- Path, query, header и body должны соответствовать wire-контракту MAX Bot API.
- Generic-параметр `MaxoMethod[Result]` - тип результата после deserialization.
- `Bot` привязывает методы через `unihttp.bind_method`. Не пиши ручные
  passthrough-методы, если достаточно `bind_method`.
- Различай `Omitted()` и `None`: `Omitted()` значит "не отправлять поле",
  `None` значит отправить `null`, если это поддерживает API.
- Для optional wire-полей используй `Omittable[T] = Omitted()`.
- Для поля, которое может прийти как `null`, используй `Omittable[T | None]`.
- Для unsafe-доступа к omitted/null полям следуй паттернам `unsafe_sender`,
  `unsafe_url` и `AttributeIsEmptyError`.
- Полиморфные типы update, attachments, markup и buttons регистрируются в
  `src/maxo/serialization.py` через `TAG_PROVIDERS`. При добавлении нового
  варианта обнови retort.
- `serialization.py` также отвечает за query dumping, defaults из
  `BotDefaults`, attachments `to_request()`, timestamps в `datetime` с `UTC` и
  привязку `Bot` через `create_retort_with_bot`.
- `MaxApiClient` добавляет российский trusted CA, `Authorization`, `User-Agent`,
  обработку ошибок API и patch для `success=false`. Не ломай эти гарантии.
- Особый случай `AddMembers` в обработке `success=false` не меняй без
  отдельного теста и обновления документации.
- `Bot.download` принимает URL или `AttachmentPayload`; сохраняет в файл или
  возвращает `BinaryIO`.
- Если меняется контракт MAX Bot API, синхронизируй метод, типы, enum,
  update-модель, facade/mixin при пользовательском удобстве, сериализацию,
  тесты и документацию.

## Тесты

- Используй `pytest`, `pytest-asyncio` в `auto` mode и `unittest.mock`.
- Для async-кода тесты тоже async. Не запускай event loop вручную без причины.
- Новая функциональность требует узких тестов рядом с соответствующей
  подсистемой: `tests/maxo`, `tests/maxo_dialog`, `tests/maxo_webhook`.
- Для `maxo.dialogs` предпочитай test tools из `src/maxo/dialogs/test_tools`:
  `BotClient`, `MockMessageManager`, memory storage и локаторы клавиатуры.
- Для webhook используй существующие fixtures в `tests/maxo_webhook`.
- Не добавляй тесты, которые требуют реального MAX API или сетевого доступа.
- Тест должен фиксировать поведение, а не внутреннюю реализацию, если только
  задача не касается внутреннего контракта.
- Для сложной логики роутинга, FSM и Bot API проверяй не только happy path, но
  и edge cases: `Omitted()`, `None`, `UNHANDLED`, `SkipHandler`, invalid states
  и ошибки API.
- При изменении Bot API и сериализации покрывай request markers, dump defaults,
  `Omitted()`, `None`, загрузку ответа/update, polymorphic dispatch и маппинг
  ошибок API.
- При изменении routing проверяй порядок обработки, `Router.include`,
  observers, middlewares, `UNHANDLED` и `SkipHandler`.
- При изменении FSM проверяй state, data, key builder и event isolation там,
  где меняется контракт хранения.
- При изменении dialogs проверяй старт, закрытие, переходы между окнами,
  callback widgets, dialog data, фоновые менеджеры и стабильность widget `id`.

## Документация и примеры

- Документация находится в `docs/` и собирается Sphinx. Основной формат страниц
  - `rst`, changelog - `docs/pages/changelog.md`.
- Новые пользовательские возможности требуют обновления docs и, если уместно,
  `examples/`.
- Примеры должны импортировать только публичный API и быть совместимыми с
  текущей версией `0.7.0`.
- При изменении структуры docs обновляй `docs/index.rst` и соответствующие
  `toctree`.
- В README держи короткие актуальные примеры. Детальные объяснения отправляй в
  `docs/pages/...`.
- Все пользовательские инструкции и примеры для ИИ в этом репозитории пиши на
  русском языке.
- В новых docs чаще используй явные observers `message_created` и
  `message_callback`; алиасы `message`, `callback_query`, `edited_message`
  упоминай как совместимость.
- Клавиатуры показывай через `maxo.utils.builders.KeyboardBuilder`.
- `magic_filter` показывай через
  `maxo.integrations.magic_filter.MagicFilter`.
- Для webhook показывай `SimpleEngine`, `AiohttpWebAdapter` или
  `FastApiWebAdapter`, `StaticRouting`, `Security`, `StaticSecretToken`,
  `collect_used_updates`.

## Что важно помнить о текущем проекте

- Проект на `uv`, не на `pip` как основном инструменте для разработки.
- Используется `justfile` для запуска команд
- `pyproject.toml` содержит строгие правила `ruff` и `mypy`.
- `src/maxo/types/` и `src/maxo/enums/` содержат много файлов, которые
  фактически являются generated API surface.
- `maxo.dialogs` и `maxo.transport.webhook` исторически портированы из
  `aiogram_dialog` и `aiogram-webhook`, поэтому рядом с изменениями нужно
  проверять совместимость паттернов.
- Для hook- и transport-изменений обязательно смотреть на тесты в
  `tests/maxo_webhook`.

## Перед PR

- Проверь рабочее дерево и не перезаписывай чужие изменения.
- Добавь тесты к измененному поведению.
- Обнови docs/examples при изменении пользовательского API.
- В PR-шаблоне честно отметь использование ИИ: код может быть написан ИИ, но
  должен пройти полный контроль человека.
- Не добавляй `Co-Authored-By`.
- Сообщения могут быть на русском, но должны оставаться понятными.

## Перед завершением задачи

Минимальный чеклист:

- Код соответствует текущим паттернам соседних файлов.
- Публичный API, docs и examples синхронизированы.
- Добавлены или обновлены тесты для измененного поведения.
- Запущены релевантные проверки. Если проверка не запускалась, явно укажи
  причину.
- Не перезаписаны чужие изменения в рабочем дереве.
