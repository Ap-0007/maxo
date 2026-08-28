from datetime import datetime

from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType


class Subscription(MaxoType):
    """
    Схема для описания подписки на WebHook

    Args:
        time: Unix timestamp в миллисекундах, когда была создана подписка
        update_types: Типы событий, на которые подписан бот
        url: URL вебхука
        version: Версия модели данных подписки
    """

    time: datetime
    """Unix timestamp в миллисекундах, когда была создана подписка"""
    url: str
    """URL вебхука"""

    update_types: list[str] | None = None
    """Типы событий, на которые подписан бот"""

    version: Omittable[str] = Omitted()
    """Версия модели данных подписки"""

    @property
    def unsafe_update_types(self) -> list[str]:
        if is_defined(self.update_types):
            return self.update_types

        raise AttributeIsEmptyError(
            obj=self,
            attr="update_types",
        )

    @property
    def unsafe_version(self) -> str:
        if is_defined(self.version):
            return self.version

        raise AttributeIsEmptyError(
            obj=self,
            attr="version",
        )
