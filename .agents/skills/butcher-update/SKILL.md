---
name: butcher-update
description: Используется при изменении контракта MAX Bot API в maxo: новой или изменённой max-swagger.json, типе, enum, методе, update либо регенерации src/maxo/types, src/maxo/enums, src/maxo/bot/methods
---

# Обновление MAX Bot API через butcher

Перед работой прочитай `butcher/AGENTS.md`. Перечень ручного слоя и его
неочевидных зависимостей находится в `references/manual-layer.md`. При
расхождении с ними выигрывают `AGENTS.md` и `butcher/AGENTS.md`.

## Основной принцип

Не запускай `just butcher` в `src/maxo` для обычного обновления контракта.
Переноси только дельту между генерацией по старой и новой спекам: полная
генерация стирает ручной слой.

## Процедура

1. Подготовь окружение и убедись, что `src/maxo` чист:

   ```bash
   uv sync --all-groups
   git status --porcelain -- src/maxo
   ```

2. Сгенерируй снимок по спеке из `HEAD` и снимок по новой спеке:

   ```bash
   mkdir -p .butcher
   git show HEAD:max-swagger.json > .butcher/spec-before.json
   just butcher --spec .butcher/spec-before.json --output-dir .butcher/before
   just butcher --output-dir .butcher/after
   diff -ru .butcher/before .butcher/after
   ```

   Если меняются базы сгенерированных классов, добавь оверрайд до создания
   `.butcher/after`.

3. Перенеси дельту вручную, сохранив ручные части файлов. Перед удалением
   исчезнувшего символа проверь его использование через `rg` в `src/`,
   `tests/`, `docs/`, `examples/` и `butcher/`.

4. Для нового update, полиморфного подтипа, метода, поля или enum пройди карту
   касаний из `butcher/AGENTS.md` и `references/manual-layer.md`. В частности,
   union из Swagger не заменяет регистрацию в `TAG_PROVIDERS`, а корректировка
   ссылки на другой тип требует `FieldOverride(ref=...)`, а не только
   `annotation`.

5. Сверь итог с новым снимком:

   ```bash
   just butcher --output-dir .butcher/check
   diff -rq src/maxo/types .butcher/check/types
   diff -rq src/maxo/enums .butcher/check/enums
   diff -rq src/maxo/bot/methods .butcher/check/bot/methods
   ```

   Допустимы только заранее известные расхождения ручного слоя. Проверяй
   конкретный список, а не историческое количество файлов.

6. Запусти проверки из `AGENTS.md`; если менялся `butcher/`, добавь
   `just butcher-test`. Форматируй только затронутые файлы:

   ```bash
   uv run ruff check --fix <затронутые файлы>
   uv run ruff check --no-fix .
   ```

## Полная перегенерация

Допустима только при изменении самого butcher и при чистом рабочем дереве.
Перед ней сохрани или закоммить нужные изменения. После генерации восстанови
ручной слой по `references/manual-layer.md` и прогони все проверки.
