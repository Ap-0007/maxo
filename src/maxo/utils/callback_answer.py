from dataclasses import dataclass
from typing import Any

from maxo.routing.ctx import Ctx
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.routing.updates.message_callback import MessageCallback

CALLBACK_ANSWER_KEY = "callback_answer"


@dataclass(slots=True)
class CallbackAnswer:
    """
    Управление авто-ответом на колбэк из хендлера.

    Middleware кладёт объект в ctx под ключом `CALLBACK_ANSWER_KEY`. Хендлер,
    объявивший параметр `callback_answer: CallbackAnswer`, может его мутировать
    до того, как middleware ответит.
    """

    disabled: bool = False
    """Не отвечать на этот колбэк."""
    before: bool = False
    """Ответить до хендлера, а не после."""
    notification: str | None = None
    """Текст одноразового уведомления (иначе пустой ответ)."""
    answered: bool = False
    """Внутреннее: ответ уже отправлен."""


class CallbackAnswerMiddleware(BaseMiddleware[MessageCallback]):
    """
    Inner-middleware: автоматически отвечает на колбэк.

    Дефолты задаются в конструкторе. Хендлер может переопределить поведение,
    мутируя `CallbackAnswer` из ctx. Аналог aiogram CallbackAnswerMiddleware,
    но без механизма flags - конфиг через мутабельный объект в ctx.
    """

    __slots__ = ("_before", "_disabled", "_notification")

    def __init__(
        self,
        before: bool = False,
        disabled: bool = False,
        notification: str | None = None,
    ) -> None:
        self._before = before
        self._disabled = disabled
        self._notification = notification

    async def __call__(
        self,
        update: MessageCallback,
        ctx: Ctx,
        next: NextMiddleware[MessageCallback],
    ) -> Any:
        answer = CallbackAnswer(
            disabled=self._disabled,
            before=self._before,
            notification=self._notification,
        )
        ctx[CALLBACK_ANSWER_KEY] = answer

        if answer.before and not answer.disabled:
            await self._answer(update, answer)

        result = await next(ctx)

        if not answer.disabled and not answer.answered:
            await self._answer(update, answer)

        return result

    async def _answer(self, update: MessageCallback, answer: CallbackAnswer) -> None:
        if answer.notification is not None:
            await update.answer(notification=answer.notification)
        else:
            await update.answer()
        answer.answered = True
