from collections.abc import Callable
from typing import Any

from adaptix import Chain, Loader, Mediator, Provider, bound, dumper, loader
from adaptix._internal.morphing.provider_template import LoaderProvider
from adaptix._internal.morphing.request_cls import LoaderRequest
from adaptix._internal.provider.loc_stack_filtering import Pred
from adaptix._internal.provider.methods_provider import method_handler
from adaptix.load_error import LoadError

from maxo._internal.adaptix.concat_provider import concat_provider

Tag = str | tuple[str, ...]


def _get_tag(data: object, tag: Tag) -> Any:
    value: Any = data
    for part in (tag,) if isinstance(tag, str) else tag:
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _matches_tag(
    actual: Any,
    value: Any | Callable[[Any], bool],
) -> bool:
    return value(actual) if callable(value) else actual == value


def _loader_has_tag(
    pred: Pred,
    tag: Tag,
    value: Any | Callable[[Any], bool],
) -> Provider:
    def loader_fn(data: dict[str, Any]) -> Any:
        actual = _get_tag(data, tag)
        if _matches_tag(actual, value):
            return data
        raise LoadError(tag, actual, value)

    return loader(pred, loader_fn, Chain.FIRST)


def _dumper_has_tag(pred: Pred, tag: str, value: Any) -> Provider:
    def dumper_fn(data: dict[str, Any]) -> Any:
        data[tag] = value
        return data

    return dumper(pred, dumper_fn, Chain.LAST)


# В Adaptix у LoaderProvider нет типизированного __init_subclass__
class _TaggedSubclassLoaderProvider(LoaderProvider):  # type: ignore[no-untyped-call]
    def __init__(
        self,
        subtype: type[Any],
        tag: Tag,
        value: Any | Callable[[Any], bool],
    ) -> None:
        self._subtype = subtype
        self._tag = tag
        self._value = value

    @method_handler
    def provide_loader(
        self,
        mediator: Mediator[Loader[Any]],
        request: LoaderRequest,
    ) -> Loader[Any]:
        base_loader = mediator.provide_from_next()
        subtype_loader = mediator.mandatory_provide(
            request.with_loc_stack(
                request.loc_stack.replace_last_type(self._subtype),
            ),
        )

        def load_tagged_subclass(data: Any) -> Any:
            actual = _get_tag(data, self._tag)
            if _matches_tag(actual, self._value):
                return subtype_loader(data)
            return base_loader(data)

        return load_tagged_subclass


def has_tag_provider(
    pred: Pred,
    tag: Tag,
    value: Any | Callable[[Any], bool],
    *,
    base: Pred | None = None,
) -> Provider:
    loader_provider = _loader_has_tag(pred, tag, value)
    if base is not None:
        if not isinstance(pred, type):
            raise TypeError("Для tagged-подтипа pred должен быть классом")
        return concat_provider(
            loader_provider,
            bound(base, _TaggedSubclassLoaderProvider(pred, tag, value)),
        )

    if not isinstance(tag, str) or callable(value):
        raise TypeError(
            "Вложенный или вычисляемый тег поддерживается только для подтипа",
        )
    return concat_provider(
        loader_provider,
        _dumper_has_tag(pred, tag, value),
    )
