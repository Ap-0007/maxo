# AGENTS.md - правила разработки maxo для AI-агентов

Этот файл обязателен для всех AI-агентов, которые работают с репозиторием
`maxo`. Все инструкции, новые skills, комментарии к разработке и документация
для агентов в этом проекте пишутся на русском языке.

`maxo` - асинхронный Python-фреймворк для разработки ботов российского
мессенджера MAX (`max.ru`). Текущая версия проекта: `0.7.0`.
Поддерживаемые версии Python: `3.12`, `3.13`, `3.14`.

## Skills

Перед изменениями подгружай профильный skill из `.agents/skills`:

- `maxo-architecture` - изменения в `src/maxo`, публичном API, роутинге, FSM,
  диалогах, транспорте и интеграциях.
- `maxo-dev-workflow` - установка окружения, локальные проверки, CI, подготовка
  PR.
- `maxo-testing` - новые и измененные тесты.
- `maxo-documentation` - документация, README, примеры и changelog.
- `maxo-bot-api` - методы Bot API, типы, enum, update-модели, сериализация,
  `unihttp` и `adaptix`.

## Команды

В текущем дереве нет `justfile`, поэтому не полагайся на `just`, даже если он
упомянут в старых документах. Используй прямые команды:

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

CI запускает lint на Python `3.14` и тесты на Python `3.12`, `3.13`, `3.14` с
разрешением зависимостей `lowest-direct` и `highest`.

## Архитектура

Ключевые директории:

| Путь | Назначение |
| --- | --- |
| `src/maxo/bot/` | `Bot`, `MaxApiClient`, состояния бота, declarative Bot API methods на `unihttp`. |
| `src/maxo/types/` | Типы MAX Bot API. Многие файлы сгенерированы по документации API. |
| `src/maxo/enums/` | Enum MAX Bot API. Многие файлы сгенерированы по документации API. |
| `src/maxo/routing/` | `Dispatcher`, `Router`, observers, handlers, filters, middlewares, facades, updates, signals. |
| `src/maxo/fsm/` | FSM: `State`, `StatesGroup`, `FSMContext`, storage, isolation, key builders. |
| `src/maxo/dialogs/` | Диалоги, портированные из `aiogram_dialog`: `Dialog`, `Window`, widgets, managers, preview, test tools. |
| `src/maxo/transport/` | Long polling и webhook engine/adapters/routing/security. |
| `src/maxo/integrations/` | Интеграции `dishka` и `magic_filter`. |
| `src/maxo/utils/` | Builders, upload helpers, formatting, deeplink/link helpers, facades. |
| `docs/` | Sphinx-документация на русском языке. |
| `examples/` | Рабочие примеры использования публичного API. |
| `tests/` | Pytest-тесты по подсистемам. |

## Главные правила разработки

- Пиши инструкции для ИИ, docstrings публичного API и пользовательскую
  документацию на русском языке.
- Используй только короткое тире `-`. Не добавляй другие Unicode-варианты тире.
- Не добавляй `Co-Authored-By` в коммиты и текст PR.
- Сохраняй строгую типизацию. `mypy` работает в `strict = true` для `src/maxo`,
  `tests` и `examples`.
- Публичный код должен быть полностью аннотирован. В тестах аннотации тоже
  проверяются mypy, хотя ruff-правила `ANN` для тестов отключены.
- Используй двойные кавычки, 4 пробела и длину строки 88 символов.
- Для внутренних путей используй `pathlib.Path`, если работа идет с файлами.
- Не добавляй top-level side effects, кроме декларативной регистрации,
  ожидаемой текущими API.
- Не прячь импорты внутрь функций без необходимости. Предпочитай обычные
  импорты на уровне модуля.
- Для новых data-моделей используй существующий стиль: наследование от
  `MaxoType` для API-моделей или `@dataclass(slots=True)` там, где в подсистеме
  уже используются dataclass.
- Не редактируй сгенерированные типы, enum и методы Bot API вручную как
  изолированную правку. Если меняется контракт API, синхронизируй методы,
  типы, сериализацию, тесты и документацию.
- Импортируй пользовательский API из публичных модулей. В документации и
  примерах не используй `maxo._internal`.
- При добавлении публичного символа обновляй соответствующий `__init__.py` и
  `__all__`, если этот модуль поддерживает явный публичный экспорт.

## Роутинг и обработка событий

- `Dispatcher` - корневой `Router`. Он добавляет workflow data, error/update
  middleware, FSM middleware и facade middleware.
- `Router.include(...)` задает порядок обхода дочерних роутеров. Первый
  обработавший обычный update останавливает дальнейший поиск.
- Сигналы `before_startup`, `after_startup`, `before_shutdown`,
  `after_shutdown` обрабатываются как lifecycle hooks, а не как обычные update.
- Observer-level filters и middleware должны соответствовать существующему
  порядку: outer middleware, filters, inner middleware, handler.
- `message`, `callback_query`, `edited_message` - алиасы для совместимости с
  привычками из aiogram. В новых документах лучше показывать явные имена
  `message_created` и `message_callback`, если это повышает ясность.
- Facade и update-модели сами умеют отвечать через mixins после привязки бота.
  Не обходи этот слой без причины.

## FSM и dialogs

- FSM включена в `Dispatcher` по умолчанию. Без явных настроек используются
  `MemoryStorage`, `SimpleEventIsolation`, `DefaultKeyBuilder`.
- Для production и нескольких процессов используй Redis storage/isolation и
  продуманную стратегию ключей.
- `maxo.dialogs` живет поверх FSM и добавляет свои observers/middlewares через
  `setup_dialogs(dp)`.
- `setup_dialogs` должен применяться к `Dispatcher` после подключения диалогов к
  роутеру.
- Для dialogs нужна изоляция с `DefaultKeyBuilder(with_destiny=True)`. В
  `setup_dialogs` это используется по умолчанию для dialog event isolation, но
  при кастомной FSM-конфигурации проверяй совместимость ключей.
- Все widget `id` внутри одного окна/диалога должны быть стабильными и
  уникальными.

## Bot API, `unihttp`, `adaptix`

- Методы Bot API - классы `MaxoMethod[Result]` с `__url__`, `__method__` и
  marker-полями из `maxo.bot.methods.markers`.
- `Bot` привязывает методы через `unihttp.bind_method`. Не пиши ручные
  passthrough-методы, если достаточно `bind_method`.
- Различай `Omitted()` и `None`: `Omitted()` значит "не отправлять поле",
  `None` значит отправить `null`, если это поддерживает API.
- Полиморфные типы update, attachments, markup и buttons регистрируются в
  `src/maxo/serialization.py` через `TAG_PROVIDERS`. При добавлении нового
  варианта обнови retort.
- `MaxApiClient` добавляет российский trusted CA, `Authorization`, `User-Agent`,
  обработку ошибок API и patch для `success=false`. Не ломай эти гарантии.
- `Bot.download` принимает URL или `AttachmentPayload`; сохраняет в файл или
  возвращает `BinaryIO`.

## Тесты

- Используй `pytest`, `pytest-asyncio` в `auto` mode и `unittest.mock`.
- Для async-кода тесты тоже async. Не запускай event loop вручную без причины.
- Новая функциональность требует узких тестов рядом с соответствующей
  подсистемой: `tests/maxo`, `tests/maxo_dialog`, `tests/maxo_webhook`.
- Для `maxo.dialogs` предпочитай test tools из `src/maxo/dialogs/test_tools`:
  `BotClient`, `MockMessageManager`, memory storage и локаторы клавиатуры.
- Для webhook используй существующие fixtures в `tests/maxo_webhook`.
- Не добавляй тесты, которые требуют реального MAX API или сетевого доступа.

## Документация и примеры

- Документация находится в `docs/` и собирается Sphinx. Основной формат страниц -
  `rst`, changelog - `docs/pages/changelog.md`.
- Новые пользовательские возможности требуют обновления docs и, если уместно,
  `examples/`.
- Примеры должны импортировать только публичный API и быть совместимыми с
  текущей версией `0.7.0`.
- При изменении структуры docs обновляй `docs/index.rst` и соответствующие
  `toctree`.
- В README держи короткие актуальные примеры. Детальные объяснения отправляй в
  `docs/pages/...`.

## Перед завершением задачи

Минимальный чеклист:

- Код соответствует текущим паттернам соседних файлов.
- Публичный API, docs и examples синхронизированы.
- Добавлены или обновлены тесты для измененного поведения.
- Запущены релевантные проверки. Если проверка не запускалась, явно укажи
  причину.
- Не перезаписаны чужие изменения в рабочем дереве.
