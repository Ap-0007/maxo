"""Рендер файлов `maxo/types/*.py` - моделей и апдейтов."""

from butcher.profile import Model
from butcher.render import docs, fields, imports


def render(model: Model) -> str:
    header = ["from typing import TypeAlias"] if model.type_aliases else []
    lines = [
        *header,
        imports.render(model.imports),
        "",
        "",
        f"class {model.name}({', '.join(model.bases)}):",
    ]

    doc = docs.render(
        docs.build_parts(
            summary=None,
            description=model.description,
            parameters=[
                (item.name, item.description)
                for item in sorted(model.fields, key=lambda field_: field_.name)
            ],
        ),
    )
    lines.extend(doc)

    body: list[str] = []
    for group in model.field_groups:
        if body:
            body.append("")
        for item in group:
            body.extend(fields.render(item))

    for item in model.fields:
        if item.unsafe:
            body.extend(fields.render_unsafe(item))

    if not body and not doc:
        body.append("    pass")

    if body and doc:
        lines.append("")
    lines.extend(body)

    for alias, comment in model.type_aliases:
        lines.extend(["", "", f"{alias}: TypeAlias = {model.name}  # {comment}"])

    return "\n".join(lines) + "\n"
