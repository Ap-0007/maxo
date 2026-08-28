from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.bot_command import BotCommand
from maxo.types.user_with_photo import UserWithPhoto


class BotInfo(UserWithPhoto):
    """
    Объект включает общую информацию о боте, URL аватара и описание. Является наследником [схемы UserWithPhoto](https://dev.max.ru/docs-api/objects/UserWithPhoto). Дополнительно к ней содержит список команд, поддерживаемых ботом. Возвращается только при вызове метода `GET /me`

    Args:
        commands: Команды, поддерживаемые ботом
        is_official: Указывает, является ли бот официальным
    """

    commands: Omittable[list[BotCommand] | None] = Omitted()
    """Команды, поддерживаемые ботом"""
    is_official: Omittable[bool] = Omitted()
    """Указывает, является ли бот официальным"""

    @property
    def unsafe_commands(self) -> list[BotCommand]:
        if is_defined(self.commands):
            return self.commands

        raise AttributeIsEmptyError(
            obj=self,
            attr="commands",
        )

    @property
    def unsafe_is_official(self) -> bool:
        if is_defined(self.is_official):
            return self.is_official

        raise AttributeIsEmptyError(
            obj=self,
            attr="is_official",
        )
