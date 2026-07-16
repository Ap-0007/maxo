from collections.abc import Awaitable, Callable, Coroutine, Mapping
from functools import wraps
from inspect import Parameter, signature
from typing import Concatenate, ParamSpec, TypeVar, overload

from maxo.routing.ctx import Ctx
from maxo.types.base import BaseUpdate

_ReturnT = TypeVar("_ReturnT")
_ParamsT = ParamSpec("_ParamsT")
_SelfT = TypeVar("_SelfT")
_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)


@overload
def inline_ctx(
    func: Callable[
        Concatenate[_SelfT, _UpdateT, Ctx, _ParamsT],
        Awaitable[_ReturnT],
    ],
) -> Callable[[_SelfT, _UpdateT, Ctx], Coroutine[object, object, _ReturnT]]: ...


@overload
def inline_ctx(
    func: Callable[Concatenate[_UpdateT, Ctx, _ParamsT], Awaitable[_ReturnT]],
) -> Callable[[_UpdateT, Ctx], Coroutine[object, object, _ReturnT]]: ...


def inline_ctx(
    func: Callable[..., Awaitable[_ReturnT]],
) -> Callable[..., Coroutine[object, object, _ReturnT]]:
    """Подставить именованные зависимости из ``ctx`` в callback."""
    parameters = tuple(signature(func).parameters.values())

    try:
        ctx_index = next(
            index
            for index, parameter in enumerate(parameters)
            if parameter.name == "ctx"
        )
    except StopIteration as error:
        msg = "Функция с @inline_ctx должна принимать параметр ctx"
        raise TypeError(msg) from error

    inline_parameters = tuple(
        parameter.name
        for parameter in parameters[ctx_index + 1 :]
        if parameter.kind
        in {Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY}
    )

    @wraps(func)
    async def wrapper(*args: object, **kwargs: object) -> _ReturnT:
        if "ctx" in kwargs:
            ctx = kwargs["ctx"]
        elif len(args) > ctx_index:
            ctx = args[ctx_index]
        else:
            msg = "Не передан обязательный параметр ctx"
            raise TypeError(msg)

        if not isinstance(ctx, Mapping):
            msg = "Параметр ctx должен быть отображением"
            raise TypeError(msg)

        inline_kwargs = {
            name: ctx[name] for name in inline_parameters if name in ctx
        }
        return await func(*args, **(kwargs | inline_kwargs))

    return wrapper
