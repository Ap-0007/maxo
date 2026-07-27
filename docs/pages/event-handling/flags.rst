Флаги
=====

.. meta::
   :description: Флаги-маркеры хендлеров в maxo: пометка обработчиков через декораторы, регистрацию и фильтры, чтение флагов из мидлварей и утилит.
   :keywords: maxo флаги, flags maxo, chat_action, rate limit бот max, маркеры хендлеров

Флаги - это маркеры на хендлерах. Сам хендлер про них не знает: флаги нужны
мидлварям и утилитам, чтобы классифицировать обработчики и вести себя по-разному
для разных хендлеров.

Типичные задачи: включить отправку действия «бот набирает сообщение» только для
долгих хендлеров, ограничить частоту вызовов конкретной команды, собрать список
всех команд бота для меню.

Как повесить флаг
-----------------

Через декоратор
^^^^^^^^^^^^^^^

Любой атрибут ``flags`` - это новый флаг с таким именем. Без вызова значением
флага становится ``True``:

.. code-block:: python

    from maxo import flags


    @flags.chat_action
    async def my_handler(update: MessageCreated) -> None: ...

Вызов с одним аргументом задаёт значение флага:

.. code-block:: python

    @flags.chat_action("sending_photo")
    async def my_handler(update: MessageCreated) -> None: ...

Вызов с именованными аргументами кладёт во флаг словарь:

.. code-block:: python

    @flags.rate_limit(rate=2, key="something")
    async def my_handler(update: MessageCreated) -> None: ...

Декораторы флагов можно складывать друг на друга, они не конфликтуют:

.. code-block:: python

    @dp.message_created(Command("report"))
    @flags.chat_action
    @flags.rate_limit(rate=5)
    async def my_handler(update: MessageCreated) -> None: ...

.. note::

    Для единообразия декоратор флага обычно размещают **ниже** декоратора
    регистрации хендлера. Реализация поддерживает оба порядка.

При регистрации хендлера
^^^^^^^^^^^^^^^^^^^^^^^^

Каждый обсёрвер принимает флаги аргументом ``flags``:

.. code-block:: python

    @dp.message_created(Command("report"), flags={"chat_action": "typing_on"})
    async def my_handler(update: MessageCreated) -> None: ...

То же самое работает и при явной регистрации:

.. code-block:: python

    dp.message_created.handler(my_handler, Command("report"), flags={"rate_limit": 5})
    dp.message_created.register(my_handler, Command("report"), flags={"rate_limit": 5})

Через фильтры
^^^^^^^^^^^^^

Фильтр, унаследованный от ``BaseFilter``, может дополнить флаги хендлера, к
которому его подключили. Для этого переопредели ``update_handler_flags``:

.. code-block:: python

    from typing import Any

    from maxo.routing.filters import BaseFilter


    class Command(BaseFilter[MessageCreated]):
        ...

        def update_handler_flags(self, flags: dict[str, Any]) -> None:
            flags["commands"] = [*flags.get("commands", ()), self]

.. note::

    Словарь флагов копируется поверхностно, поэтому не мутируй уже лежащие в нём
    списки и словари - собирай новое значение, иначе правка утечёт во флаги
    других хендлеров и в словарь, переданный в ``flags={...}``.

Так работает встроенный фильтр :class:`~maxo.routing.filters.Command`: он кладёт
себя во флаг ``commands``.

Приоритет
^^^^^^^^^

Если один и тот же флаг задан несколькими способами, побеждает тот, что ближе к
самой функции. Приоритет по убыванию:

1. флаги от декораторов на функции,
2. флаги от фильтров,
3. ``flags={...}`` при регистрации хендлера.

Как прочитать флаг
------------------

Флаги доступны в фильтрах хендлера и **inner**-мидлварях: к моменту их
выполнения хендлер уже выбран и лежит в ``ctx`` под ключом ``handler``. В
**outer**-мидлварях и в фильтрах обсёрвера (``router.message_created.filter``)
хендлер ещё не известен, поэтому флагов там нет.

.. code-block:: python

    from typing import Any

    from maxo import Ctx
    from maxo.routing.flags import get_flag
    from maxo.routing.interfaces import BaseMiddleware, NextMiddleware
    from maxo.types import MessageCreated


    class RateLimitMiddleware(BaseMiddleware[MessageCreated]):
        async def __call__(
            self,
            update: MessageCreated,
            ctx: Ctx,
            next: NextMiddleware[MessageCreated],
        ) -> Any:
            rate_limit = get_flag(ctx, "rate_limit")
            if rate_limit is None:  # хендлер не помечен - пропускаем без ограничений
                return await next(ctx)

            ...
            return await next(ctx)


    dp.message_created.middleware(RateLimitMiddleware())  # именно inner

Флаги можно проверять и магическим фильтром - для этого нужен экстра
``maxo[magic_filter]``:

.. code-block:: python

    from magic_filter import F

    from maxo.routing.flags import check_flags

    if check_flags(ctx, F.chat_action.action == "sending_photo"):
        ...

Использование в утилитах
------------------------

Флаги доступны и вне обработки апдейта - прямо у зарегистрированных хендлеров.
Например, так можно обойти всё дерево роутеров и собрать команды бота, которые
фильтр ``Command`` положил во флаг ``commands``:

.. code-block:: python

    from collections.abc import Iterator

    from maxo import Router
    from maxo.routing.filters import Command


    def collect_commands(router: Router) -> Iterator[str]:
        for handler in router.message_created.handlers:
            for command in handler.flags.get("commands", []):
                yield from (str(name) for name in command.commands)

        for child_router in router.children_routers:
            if isinstance(child_router, Router):
                yield from collect_commands(child_router)

Дальше из этого списка собирается меню команд бота через
``bot.edit_my_commands(commands=...)``.

Флаги в самом maxo
------------------

* ``chat_action`` - :doc:`../utils/chat_action`,
* ``callback_answer`` - :doc:`../utils/callback_answer`,
* ``commands`` - заполняется фильтром :class:`~maxo.routing.filters.Command`.

Справочник
----------

.. automodule:: maxo.routing.flags
   :members: flags, FlagGenerator, FlagDecorator, Flag, extract_flags, extract_flags_from_object, get_flag, check_flags
   :undoc-members:
   :show-inheritance:
