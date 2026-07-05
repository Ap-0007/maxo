from abc import ABC, abstractmethod

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
        """
        Размер файла в байтах.

        По умолчанию читает файл целиком.
        Наследники, которые знают размер дёшево, должны переопределить метод.
        """
        return len(await self.read())
