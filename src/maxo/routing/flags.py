"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/dispatcher/flags.py.

Original code licensed under MIT by aiogram contributors

The MIT License (MIT)

Copyright (c) 2017 - present Alex Root Junior

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
"""

import inspect
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, cast, overload

from maxo.routing.interfaces.filter import Filter

if TYPE_CHECKING:
    from magic_filter import MagicFilter

    from maxo.routing.interfaces.handler import Handler

    FlagsSource = Handler[Any, Any] | MutableMapping[str, Any] | None

FLAG_ATTR_NAME: Final = "maxo_flag"
"""Имя атрибута, в котором декораторы флагов хранят флаги на функции-хендлере."""

HANDLER_KEY: Final = "handler"
"""Ключ ctx, под которым лежит текущий хендлер во время фильтрации и обработки."""


class AttrDict(dict[str, Any]):
    """
    Словарь с доступом к значениям через атрибуты.

    Нужен, чтобы `magic_filter` мог обращаться к значениям флага как к атрибутам,
    например `F.chat_action.action`. Повторяет `magic_filter.AttrDict`, потому что
    `magic_filter` - опциональная зависимость `maxo`.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    if TYPE_CHECKING:
        # Значения читаются как атрибуты, но их имена известны только в рантайме
        def __getattr__(self, name: str) -> Any: ...


@dataclass(frozen=True, slots=True)
class Flag:
    """Пара «имя флага - значение флага»."""

    name: str
    value: Any


@dataclass(frozen=True, slots=True)
class FlagDecorator:
    """
    Декоратор, навешивающий флаг на функцию-хендлер.

    Вызов с функцией навешивает флаг, вызов со значением или именованными
    аргументами возвращает новый декоратор с этим значением.
    """

    flag: Flag

    @classmethod
    def _with_flag(cls, flag: Flag) -> "FlagDecorator":
        return cls(flag)

    def _with_value(self, value: Any) -> "FlagDecorator":
        return self._with_flag(Flag(self.flag.name, value))

    @overload
    def __call__(self, value: Callable[..., Any], /) -> Callable[..., Any]: ...

    @overload
    def __call__(self, value: Any, /) -> "FlagDecorator": ...

    @overload
    def __call__(self, **kwargs: Any) -> "FlagDecorator": ...

    def __call__(
        self,
        value: Any | None = None,
        **kwargs: Any,
    ) -> "Callable[..., Any] | FlagDecorator":
        if value is not None and kwargs:
            raise ValueError(
                "Аргументы `value` и `**kwargs` нельзя использовать вместе",
            )

        if value is not None and callable(value):
            setattr(
                value,
                FLAG_ATTR_NAME,
                {
                    **extract_flags_from_object(value),
                    self.flag.name: self.flag.value,
                },
            )
            return cast(Callable[..., Any], value)

        return self._with_value(AttrDict(kwargs) if value is None else value)


if TYPE_CHECKING:

    class _ChatActionFlagProtocol(FlagDecorator):
        @overload
        def __call__(self, value: Callable[..., Any], /) -> Callable[..., Any]: ...

        @overload
        def __call__(self, value: Any, /) -> FlagDecorator: ...

        @overload
        def __call__(
            self,
            *,
            action: str = ...,
            interval: float = ...,
            initial_sleep: float = ...,
            **kwargs: Any,
        ) -> FlagDecorator: ...

        def __call__(
            self,
            value: Any | None = None,
            **kwargs: Any,
        ) -> "Callable[..., Any] | FlagDecorator": ...

    class _CallbackAnswerFlagProtocol(FlagDecorator):
        @overload
        def __call__(self, value: Callable[..., Any], /) -> Callable[..., Any]: ...

        @overload
        def __call__(self, value: Any, /) -> FlagDecorator: ...

        @overload
        def __call__(
            self,
            *,
            disabled: bool = ...,
            before: bool = ...,
            notification: str | None = ...,
            **kwargs: Any,
        ) -> FlagDecorator: ...

        def __call__(
            self,
            value: Any | None = None,
            **kwargs: Any,
        ) -> "Callable[..., Any] | FlagDecorator": ...


class FlagGenerator:
    """
    Генератор декораторов флагов.

    Любой атрибут - это новый флаг с этим именем и значением `True`:

    ```python
    from maxo import flags


    @flags.chat_action
    async def handler(update: MessageCreated) -> None: ...
    ```
    """

    __slots__ = ()

    def __getattr__(self, name: str) -> FlagDecorator:
        if name.startswith("_"):
            raise AttributeError("Имя флага не должно начинаться с подчёркивания")
        return FlagDecorator(Flag(name=name, value=True))

    if TYPE_CHECKING:
        chat_action: _ChatActionFlagProtocol
        callback_answer: _CallbackAnswerFlagProtocol


flags = FlagGenerator()
"""Точка входа для навешивания флагов на хендлеры."""


def extract_flags_from_object(obj: Any) -> dict[str, Any]:
    """
    Достаёт флаги, навешенные декораторами на объект.

    Args:
        obj: функция-хендлер или любой другой объект.

    Returns:
        Словарь флагов, пустой если флагов нет.

    """
    obj_flags = getattr(obj, FLAG_ATTR_NAME, None)
    if obj_flags is None:
        return {}
    return cast(dict[str, Any], obj_flags)


def resolve_handler_flags(
    handler_fn: Callable[..., Any],
    filters: Sequence[Filter[Any]] = (),
    flags: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Собирает итоговые флаги хендлера.

    Приоритет по возрастанию: явно переданные `flags`, флаги от фильтров,
    флаги от декораторов на функции-хендлере.

    Args:
        handler_fn: функция-хендлер.
        filters: фильтры хендлера.
        flags: флаги, переданные при регистрации.

    Returns:
        Словарь флагов хендлера.

    """
    resolved: dict[str, Any] = dict(flags) if flags else {}

    for filter_ in filters:
        update_handler_flags = getattr(filter_, "update_handler_flags", None)
        if update_handler_flags is not None:
            update_handler_flags(resolved)

    # Флаги ищутся и на обёртке, и под ней: декоратор флага мог оказаться как
    # выше, так и ниже декоратора, оборачивающего хендлер
    resolved.update(extract_flags_from_object(inspect.unwrap(handler_fn)))
    resolved.update(extract_flags_from_object(handler_fn))
    return resolved


def extract_flags(source: "FlagsSource") -> dict[str, Any]:
    """
    Достаёт флаги из хендлера или из ctx.

    Args:
        source: хендлер или ctx мидлвари/фильтра.

    Returns:
        Словарь всех флагов хендлера, пустой если флагов нет.

    """
    if isinstance(source, MutableMapping) and HANDLER_KEY in source:
        source = source[HANDLER_KEY]

    source_flags = getattr(source, "flags", None)
    if source_flags is None:
        return {}
    return cast(dict[str, Any], source_flags)


def get_flag(
    source: "FlagsSource",
    name: str,
    *,
    default: Any | None = None,
) -> Any:
    """
    Достаёт значение флага по имени.

    Args:
        source: хендлер или ctx мидлвари/фильтра.
        name: имя флага.
        default: значение по умолчанию, если флага нет.

    Returns:
        Значение флага или `default`.

    """
    return extract_flags(source).get(name, default)


def check_flags(source: "FlagsSource", magic: "MagicFilter") -> Any:
    """
    Проверяет флаги магическим фильтром.

    Args:
        source: хендлер или ctx мидлвари/фильтра.
        magic: магический фильтр из `magic_filter`.

    Returns:
        Результат применения магического фильтра к флагам.

    """
    return magic.resolve(AttrDict(extract_flags(source)))
