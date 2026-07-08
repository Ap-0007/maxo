from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from maxo.enums import UploadType


class InputFile(ABC):
    __slots__ = ()

    @property
    @abstractmethod
    def file_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def type(self) -> UploadType:
        raise NotImplementedError

    @abstractmethod
    async def read(self) -> bytes:
        raise NotImplementedError

    async def size(self) -> int:
        """Размер файла в байтах."""
        return len(await self.read())

    async def stream(self, chunk_size: int) -> AsyncIterator[bytes]:
        """Содержимое файла кусками по `chunk_size` байт."""
        data = await self.read()
        for start in range(0, len(data), chunk_size):
            yield data[start : start + chunk_size]
