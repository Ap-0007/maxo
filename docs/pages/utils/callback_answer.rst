Авто-ответ на колбэк
====================

``CallbackAnswerMiddleware`` автоматически отвечает на ``MessageCallback`` (колбэк от нажатия инлайн-кнопки).
Порт ``CallbackAnswerMiddleware`` из ``aiogram``.

Подключение
-----------

Middleware - внутренний (inner), вешается на обсёрвер ``message_callback``:

.. code-block:: python

    from maxo import Dispatcher
    from maxo.utils.callback_answer import CallbackAnswerMiddleware

    dp = Dispatcher()
    dp.message_callback.middleware(CallbackAnswerMiddleware())

По умолчанию middleware отвечает пустым ответом **после** хендлера. Ответ
отправляется даже если хендлер бросил исключение.

Настройка через флаги
---------------------

Дефолты из конструктора переопределяются для конкретного хендлера флагом
``callback_answer`` (подробнее про флаги - :doc:`../event-handling/flags`):

.. code-block:: python

    from maxo import flags


    @dp.message_callback()
    @flags.callback_answer(notification="Готово!")
    async def handler(update: MessageCallback) -> None: ...


    @dp.message_callback()
    @flags.callback_answer(disabled=True)  # отвечаем на колбэк сами
    async def manual_handler(update: MessageCallback) -> None: ...

Словарь во флаге понимает ключи ``disabled``, ``before`` и ``notification``.
Голый ``@flags.callback_answer`` включает авто-ответ - это удобно, если мидлварь
подключена с ``disabled=True`` и авто-ответ нужен точечно. Обратный случай -
``@flags.callback_answer(False)``: он выключает авто-ответ для одного хендлера.

Управление из хендлера
----------------------

Middleware кладёт в ctx мутабельный ``CallbackAnswer`` под ключом
``callback_answer``. Хендлер, объявивший параметр ``callback_answer``, может
поменять поведение до того, как middleware ответит:

.. code-block:: python

    from maxo.routing.updates import MessageCallback
    from maxo.utils.callback_answer import CallbackAnswer


    @dp.message_callback()
    async def handler(
        update: MessageCallback,
        callback_answer: CallbackAnswer,
    ) -> None:
        callback_answer.notification = "Готово!"  # текст всплывашки
        # callback_answer.disable()               # не отвечать вовсе

После отправки ответа ``CallbackAnswer`` становится неизменяемым: запись в любое
поле поднимает ``CallbackAnswerException``.

.. automodule:: maxo.utils.callback_answer
   :members:
   :undoc-members:
   :show-inheritance:
