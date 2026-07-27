Действия бота в чате
====================

.. meta::
   :description: ChatActionSender и ChatActionMiddleware в maxo: автоматическая отправка действий «бот набирает сообщение» и «бот отправляет файл» во время долгих операций.
   :keywords: maxo chat action, ChatActionSender, ChatActionMiddleware, typing_on, sending_file, бот max набирает сообщение

MAX показывает действие бота (``typing_on``, ``sending_photo`` и другие)
ограниченное время, поэтому во время долгой операции его надо переотправлять.
``ChatActionSender`` делает это за вас в фоновой задаче.

Порт ``ChatActionSender`` и ``ChatActionMiddleware`` из ``aiogram``.

Отправщик
---------

``ChatActionSender`` - асинхронный контекстный менеджер: пока выполняется код
внутри ``async with``, в чат раз в ``interval`` секунд уходит действие.

.. code-block:: python

    from maxo.utils.chat_action import ChatActionSender


    @dp.message_created(Command("report"))
    async def report_handler(update: MessageCreated, bot: Bot) -> None:
        async with ChatActionSender.typing_on(bot=bot, chat_id=update.chat_id):
            result = await build_long_report()

        await update.answer(text=result)

Готовые фабрики под каждое действие: ``typing_on``, ``sending_photo``,
``sending_video``, ``sending_audio``, ``sending_file`` и ``mark_seen``. Любое
действие можно задать и напрямую через ``action``:

.. code-block:: python

    from maxo.enums import SenderAction

    async with ChatActionSender(
        bot=bot,
        chat_id=chat_id,
        action=SenderAction.SENDING_FILE,
        interval=3,  # как часто переотправлять действие
        initial_sleep=1,  # не мигать действием, если работа окажется быстрой
    ):
        ...

Мидлварь
--------

``ChatActionMiddleware`` избавляет от ``async with`` в каждом хендлере.
Регистрируется как **внутренняя** (inner) мидлварь - только так ей доступны
флаги хендлера:

.. code-block:: python

    from maxo.utils.chat_action import ChatActionMiddleware

    dp.message_created.middleware(ChatActionMiddleware())

После этого все хендлеры, которые работают дольше ``initial_sleep``, будут
показывать ``typing_on``.

Дефолты отправщика задаются в конструкторе мидлвари. Ненулевой ``initial_sleep``
стоит поставить сразу: иначе каждый быстрый хендлер тратит лишний запрос к API
на действие, которое никто не успеет увидеть.

.. code-block:: python

    dp.message_created.middleware(ChatActionMiddleware(initial_sleep=1))

Настройка через флаги
---------------------

Поведение конкретного хендлера настраивается флагом ``chat_action``
(подробнее про флаги - :doc:`../event-handling/flags`).

Поменять только тип действия:

.. code-block:: python

    from maxo import flags


    @dp.message_created(Command("photo"))
    @flags.chat_action("sending_photo")
    async def my_handler(update: MessageCreated) -> None: ...

Настроить отправщик целиком:

.. code-block:: python

    @dp.message_created(Command("file"))
    @flags.chat_action(action="sending_file", interval=3, initial_sleep=1)
    async def my_handler(update: MessageCreated) -> None: ...

Выключить отправку для конкретного хендлера:

.. code-block:: python

    @dp.message_created(Command("fast"))
    @flags.chat_action(False)
    async def my_handler(update: MessageCreated) -> None: ...

Мидлварь определяет чат по ``update_context`` из ``ctx``, а если его нет - по
самому апдейту. Если ID чата определить не удалось, мидлварь просто пропускает
апдейт дальше, ничего не отправляя.

Справочник
----------

.. automodule:: maxo.utils.chat_action
   :members:
   :undoc-members:
   :show-inheritance:
