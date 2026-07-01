---
name: maxo-dev-workflow
description: Используй при настройке окружения maxo, запуске проверок, анализе CI, подготовке PR, релизных и рабочих команд разработки.
---

# Рабочий процесс разработки maxo

## Окружение

Проект использует `uv`. Поддерживаемые версии Python: `3.12`, `3.13`, `3.14`.

```bash
uv sync --all-groups
```

В текущем репозитории нет `justfile`. Не запускай `just` как обязательную
команду, даже если старые документы его упоминают.

## Основные проверки

```bash
uv run ruff check --no-fix .
uv run mypy --config-file pyproject.toml
uv run pytest tests/ --cov=src --cov-report=term
```

Полная тестовая матрица через `nox`:

```bash
uv run nox -s test
```

Точечно:

```bash
uv run pytest tests/maxo/routing/test_payload.py -v
uv run pytest tests/maxo_dialog/test_create.py::test_name -v
uv run ruff check --no-fix src/maxo/path.py tests/path/test_file.py
```

`pyproject.toml` содержит `tool.ruff.fix = true`, поэтому для проверки без
изменения файлов используй `ruff check --no-fix`.

## CI

- `.github/workflows/lint.yml`:
  - Python `3.14`.
  - `uv pip install -e . --group=dev --system`.
  - `ruff check --no-fix .`.
  - `mypy --config-file pyproject.toml`.
- `.github/workflows/test.yml`:
  - Python `3.12`, `3.13`, `3.14`.
  - Dependency resolution: `lowest-direct` и `highest`.
  - `uv sync --all-groups --resolution ...`.
  - `uv run pytest tests/ --cov=src --cov-report=xml --cov-report=term`.

## Перед PR

- Проверь рабочее дерево и не перезаписывай чужие изменения.
- Добавь тесты к измененному поведению.
- Обнови docs/examples при изменении пользовательского API.
- В PR-шаблоне честно отметь использование ИИ: код может быть написан ИИ, но
  должен пройти полный контроль человека.
- Не добавляй `Co-Authored-By`.
- Сообщения коммитов могут быть на русском, но должны оставаться понятными.

## Локальные зависимости

Опциональные extras:

- `maxo[magic_filter]`
- `maxo[dishka]`
- `maxo[redis]`
- `maxo[fastapi]`
- `maxo[preview]`

Dev-группа включает lint, tests, docs и основные extras. Если тест требует
конкретный extra, сначала проверь, что он установлен через `uv sync --all-groups`.
