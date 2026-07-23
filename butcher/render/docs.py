"""
Docstring'и в стиле maxo: описание, блок ``Args:`` и ссылка на источник.

Стиль отличается от генераторного (`render/serializers/base.py:docstring`): тот
переформатирует абзацы по ширине и ломает markdown, который приходит из спеки.
Здесь текст сохраняется как есть, меняются только тире, ссылки и переносы.
"""

import re

DOC_BASE_URL = "https://dev.max.ru"

# Ссылки в спеке относительные от корня сайта: `](/docs-api/methods/...)`,
# `](/docs-api#Якорь)`, `](/docs/webapps/bridge#WebAppData)`.
_LINK_PATTERN = re.compile(r"]\((/[^)]*)\)")
_NORMALIZED = {
    0x2010: "-",  # hyphen
    0x2011: "-",  # non-breaking hyphen
    0x2012: "-",  # figure dash
    0x2013: "-",  # en dash
    0x2014: "-",  # em dash
    0x2015: "-",  # horizontal bar
    0x2212: "-",  # minus sign
    0x00A0: " ",  # non-breaking space
}


def convert_links(text: str) -> str:
    """Развернуть относительные ссылки на документацию в абсолютные."""
    return _LINK_PATTERN.sub(rf"]({DOC_BASE_URL}\1)", text)


def normalize(text: str) -> str:
    """Привести к обычному дефису все Unicode-тире (и nbsp - к пробелу)."""
    return text.translate(_NORMALIZED)


def clean(text: str) -> str:
    """Подготовить кусок текста из спеки к вставке в docstring."""
    return convert_links(
        normalize(text)
        .strip()
        .replace("<br>", "\n")
        .replace("</br>", "\n")
        .replace("<br/>", "\n")
        .replace('"""', "'''"),
    )


def build_parts(
    summary: str | None,
    description: str | None,
    parameters: list[tuple[str, str | None]],
    source_link: str | None = None,
) -> list[str]:
    """Собрать строки docstring'а класса."""
    parts: list[str] = []

    if summary:
        parts.append(clean(summary))

    if description:
        if parts and parts[-1] != "":
            parts.append("")
        parts.extend(clean(description).split("\n"))

    if parameters:
        if parts and parts[-1] != "":
            parts.append("")
        parts.append("Args:")
        for name, raw in parameters:
            text = clean(raw).replace("\n\n", "\n") if raw else ""
            text = text.replace("\n", "\n        ")
            parts.append(f"    {name}: {text}")

    if source_link:
        if parts and parts[-1] != "":
            parts.append("")
        parts.append(f"Источник: {source_link}")

    return parts


def render(parts: list[str], indent: str = "    ") -> list[str]:
    """Готовые строки docstring'а вместе с тройными кавычками (или пустой список)."""
    if not parts:
        return []

    lines: list[str] = []
    for part in parts:
        if part:
            lines.extend(f"{indent}{line}".rstrip() for line in part.split("\n"))
        else:
            lines.append("")
    while lines and not lines[-1].strip():
        lines.pop()

    if len(lines) == 1:
        return [f'{indent}"""{lines[0].strip()}"""']
    return [f'{indent}"""', *lines, f'{indent}"""']


def render_field(description: str | None, indent: str = "    ") -> list[str]:
    """Docstring под полем: однострочный или блоком."""
    if not description:
        return []
    text = clean(description)
    if "\n" not in text:
        return [f'{indent}"""{text}"""']
    body = [f"{indent}{line}" if line else "" for line in text.split("\n")]
    return [f'{indent}"""', *body, f'{indent}"""']
