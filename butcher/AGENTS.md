# AGENTS.md - butcher, кодогенерация maxo

Правила для AI-агентов, работающих с `butcher/`. Дополняет корневой
`AGENTS.md`, а не заменяет его: общие правила проекта (русский язык, короткое
тире, строгая типизация, conventional commits) действуют и здесь.

Butcher генерирует `src/maxo/types`, `src/maxo/enums` и `src/maxo/bot/methods`
из `max-swagger.json` в корне репозитория. Этот файл - единственный источник
правды по контракту MAX Bot API.

## Команды

```bash
just butcher       # генерация в src/maxo
just butcher-test  # тесты butcher (31 шт.)
just butcher-init  # git submodule update --init, если каталог генератора пуст
```

`just butcher` принимает аргументы CLI, например
`just butcher --output-dir /tmp/maxo-gen` - удобно, чтобы посмотреть вывод, не
трогая рабочее дерево, или `--spec <путь или URL>` для другой спеки.

## Как это устроено

Butcher **не разбирает свагер сам**. За `allOf`, `oneOf`/`anyOf`, `nullable` в
обеих формах (3.0 `nullable: true` и 3.1 `type: [x, "null"]`), форматы,
дефолты, `readOnly`, дискриминаторы, тела запросов, внешние `$ref` и коллизии
имён отвечает `unihttp-openapi-generator` - сабмодуль
`butcher/unihttp-openapi-generator` (форк `goduni/unihttp-openapi-generator`).
Он строит IR - типизированное промежуточное представление, независимое от
того, во что потом рендерится код.

За butcher остаётся только то, чем maxo отличается от голого свагера.

```text
max-swagger.json
  -> spec.load()            загрузка + build_ir (генератор)
  -> profile.build_profile()  maxo-трансформации IR
  -> render/*                 стиль вывода maxo
  -> emit.write()             запись в src/maxo + ruff
```

| Модуль          | Назначение                                                                 |
|-----------------|----------------------------------------------------------------------------|
| `spec.py`       | Загрузка спеки и построение IR. Здесь же выбираются флаги генератора.       |
| `profile.py`    | Трансформации IR в структуры `Model`/`Enum`/`Unions`/`Method`.              |
| `overrides.py`  | Декларативные таблицы отличий maxo от свагера. Только данные, без логики.   |
| `naming.py`     | Имена классов и пути модулей внутри пакета `maxo`.                          |
| `render/`       | Печать кода: типы, enum'ы, union-файлы, методы, `__init__.py`, docstring'и. |
| `emit.py`       | Запись файлов и форматирование через `ruff` (конфигом проекта).             |
| `__main__.py`   | CLI на argparse.                                                            |
| `tests/`        | Тесты профиля и рендера на маленькой фикстуре-спеке.                        |

### Флаги генератора

IR строится с двумя обязательными для maxo флагами (`spec.py`):

- `inheritance=True` - поля родителя остаются у родителя, подтипы наследуются.
  Без него `PhotoAttachment` получил бы копию полей `Attachment`, а сама база
  превратилась бы в union-алиас.
- `omit_optionals=True` - необязательные поля остаются
  `Omittable[...] = Omitted()`, а не схлопываются в `T | None = None`.

## Слой оверрайдов

`overrides.py` - место для всего, чем maxo намеренно отличается от свагера:

- `SKIP_SCHEMAS` / `SKIP_ENUMS` / `SKIP_OPERATIONS` - что не генерировать.
  Пропуск базы каскадом уносит всех её наследников.
- `REPLACED_BASES` - схема, чей файл не генерируется, но подтипы остаются
  (`Update` -> ручной `MaxUpdate`). Каскада, в отличие от `SKIP_SCHEMAS`, нет.
- `UNION_FILES` + `BASE_TO_UNION` - состав `attachments.py`, `buttons.py`,
  `markup_elements.py`, `updates.py` и чем заменяется ссылка на базу в
  аннотациях полей.
- `ENUM_EXTRAS` - самодельные члены enum'ов и aiogram-алиасы
  (`AttachmentType.TEXT`, `SenderAction.MARK_SEEN`, `ParseMode`, `ContentType`).
- `TYPE_ALIASES` - алиасы уровня модуля внутри сгенерированного типа
  (`CallbackQuery = MessageCallback`).
- `CLASS_MIXINS` - фасады в базах классов (`MessageMethodsFacade` и другие).
- `TYPES_EXTRA_EXPORTS` / `METHODS_EXTRA_EXPORTS` - ручные символы, которые
  должны попасть в сгенерированные `__init__.py`.
- `INLINE_ALIASES`, `TIMESTAMP_HINTS` - мелкие правила типов.

**Главное правило: если после генерации приходится править файл руками
одинаковым образом - правь таблицу в `overrides.py`, а не `src/maxo`.**

## Что остаётся ручным

Butcher не создаёт и при генерации затрёт, если файл лежит на его пути:

- `src/maxo/types/base.py` (`MaxoType`, `MaxUpdate`, `BotMixin`).
- `factory()` и `to_request()` у attachment-типов, `generated_url` у
  `Message`, `keyboard`/`content_type` у `MessageBody` и подобные хелперы.
- Методы вне свагера: `GetChatByLink`, `DeleteChat`, `UploadMedia`,
  `EditBotInfo`, `GetChats`, `SetAdmins`.
- Кастомные хвосты методов: `GetUpdates.make_response`,
  `UploadMedia.validate_response`.
- `serialization.py` (`TAG_PROVIDERS`) и `warming_up.py` - butcher их не
  трогает, но при новом полиморфном типе их нужно обновить руками.

Рабочий процесс: `just butcher` пишет прямо в `src/maxo`, дальше результат
ревьюится через `git diff` и ручные куски восстанавливаются точечно.

## Правила разработки

- Логика - в `profile.py`, данные - в `overrides.py`. Не зашивай конкретные
  имена схем в код профиля.
- Если проблема в самом генераторе - чини её в сабмодуле и оформляй PR в
  апстрим, а не обходи костылём в butcher. Так уже сделаны `--inheritance`,
  `IRBodyField.description` и отказ от суффикса у soft keywords.
- Правки в сабмодуле подхватываются сразу: `just butcher` ставит его через
  `uv run --with-editable`.
- Butcher не входит в `mypy` (`files` в `pyproject.toml`), но проверяется
  `ruff` с конфигом проекта. Сам сабмодуль из `ruff` исключён.
- Тесты butcher не попадают в автосбор `pytest` (`testpaths = ["tests"]`) и
  запускаются только через `just butcher-test`. Им нужен установленный
  генератор.
- Новую трансформацию профиля закрывай тестом в `tests/test_profile.py`, новую
  форму вывода - в `tests/test_render.py`. Фикстура-спека живёт в
  `tests/conftest.py` и намеренно урезана: профиль должен переживать спеку, в
  которой нет части схем из таблиц оверрайдов.

## Проверка результата

1. Прогон в сторону: `just butcher --output-dir /tmp/maxo-gen`, затем
   `diff -ru src/maxo /tmp/maxo-gen`.
2. `just butcher-test`.
3. После генерации в `src/maxo`: `just lint`, `just mypy`, `just test` и
   `PYTHONPATH=src uv run python -c "import maxo"` (ловит циклы импортов).
