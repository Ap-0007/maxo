from abc import abstractmethod
from typing import Any, Protocol, TypeVar, runtime_checkable

from maxo.routing.ctx import Ctx
from maxo.routing.updates.base import BaseUpdate

_UpdateT_co = TypeVar("_UpdateT_co", bound=BaseUpdate, covariant=True)
_UpdateT_contra = TypeVar("_UpdateT_contra", bound=BaseUpdate, contravariant=True)


@runtime_checkable
class NextMiddleware(Protocol[_UpdateT_co]):
    __slots__ = ()

    @abstractmethod
    async def __call__(self, ctx: Ctx) -> Any:
        raise NotImplementedError


@runtime_checkable
class BaseMiddleware(Protocol[_UpdateT_contra]):
    __slots__ = ()

    @abstractmethod
    async def __call__(
        self,
        update: _UpdateT_contra,
        ctx: Ctx,
        next: NextMiddleware[_UpdateT_contra],
    ) -> Any:
        raise NotImplementedError
