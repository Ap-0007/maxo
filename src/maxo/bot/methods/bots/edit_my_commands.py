from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Body
from maxo.omit import Omittable, Omitted
from maxo.types.bot_command import BotCommand
from maxo.types.bot_commands_info import BotCommandsInfo


class EditMyCommands(MaxoMethod[BotCommandsInfo]):
    """
    Редактирование команд бота

    Метод добавляет, изменяет или удаляет команды бота, отображаемые пользователю в качестве подсказок при вводе « `/` »

     Для удаления команд передайте пустой массив `commands`

    #### Пример запроса:
    ```bash
    curl -X  "https://platform-api2.max.ru/me/commands" \
      -H "Authorization: {access_token}" \
      -H "Content-Type: application/json" \
      -d '{
            "commands": [
              {
                "name": "string",
                "description": "string"
              }
            ]
          }'
    ```

    Args:
        commands: Список команд и их описаний, отображаемых пользователю в подсказках при вводе « `/` »

    Источник: https://dev.max.ru/docs-api/methods/PATCH/me/commands
    """

    __url__ = "me/commands"
    __method__ = "patch"

    commands: Body[Omittable[list[BotCommand]]] = Omitted()
    """Список команд и их описаний, отображаемых пользователю в подсказках при вводе « `/` »"""
