"""Запись сгенерированных модулей в дерево `src/maxo`."""

from pathlib import Path

from unihttp_openapi_generator.postprocess import format_path, format_python

from butcher import overrides
from butcher.profile import MaxoDocument
from butcher.render import enums, inits, methods, types, unions


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_python(source, filename=path.name), encoding="utf-8")


def write(document: MaxoDocument, output_dir: Path) -> list[Path]:
    """Записать типы, enum'ы, union-файлы и методы. Возвращает список файлов."""
    types_dir = output_dir / "types"
    enums_dir = output_dir / "enums"
    methods_dir = output_dir / "bot" / "methods"
    written: list[Path] = []

    for model in document.models:
        path = types_dir / f"{model.module_stem}.py"
        _write(path, types.render(model))
        written.append(path)

    for union_file in document.unions:
        path = types_dir / f"{union_file.module}.py"
        _write(path, unions.render(union_file))
        written.append(path)

    for enum in document.enums:
        path = enums_dir / f"{enum.module_stem}.py"
        _write(path, enums.render(enum))
        written.append(path)

    for method in document.methods:
        path = methods_dir / method.tag / f"{method.module_stem}.py"
        _write(path, methods.render(method))
        written.append(path)

    for tag in {method.tag for method in document.methods}:
        # Пустой файл-маркер пакета: реэкспорт живёт в `bot/methods/__init__.py`.
        (methods_dir / tag / "__init__.py").touch()

    _write(
        types_dir / "__init__.py",
        inits.types(document, overrides.TYPES_EXTRA_EXPORTS),
    )
    _write(enums_dir / "__init__.py", inits.enums(document))
    _write(
        methods_dir / "__init__.py",
        inits.methods(document, overrides.METHODS_EXTRA_EXPORTS),
    )
    written.extend(
        [
            types_dir / "__init__.py",
            enums_dir / "__init__.py",
            methods_dir / "__init__.py",
        ],
    )

    # Проектный проход ruff: сортировка импортов с учётом настроек репозитория.
    format_path(output_dir)
    return written
