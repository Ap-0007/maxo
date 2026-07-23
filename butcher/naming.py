"""Имена и пути модулей в пакете maxo."""

from unihttp_openapi_generator.ir.naming import to_snake_case

TYPES_PACKAGE = "maxo.types"
ENUMS_PACKAGE = "maxo.enums"
METHODS_PACKAGE = "maxo.bot.methods"


def module_stem(class_name: str) -> str:
    """Имя файла для класса: ``PhotoAttachment`` -> ``photo_attachment``."""
    return to_snake_case(class_name)


def type_module(class_name: str) -> str:
    return f"{TYPES_PACKAGE}.{module_stem(class_name)}"


def enum_module(class_name: str) -> str:
    return f"{ENUMS_PACKAGE}.{module_stem(class_name)}"


def method_module(tag: str, class_name: str) -> str:
    return f"{METHODS_PACKAGE}.{tag}.{module_stem(class_name)}"


def enum_member(value: str) -> str:
    """Имя члена enum: ``inline_keyboard`` -> ``INLINE_KEYBOARD``."""
    return value.upper().replace("-", "_")
