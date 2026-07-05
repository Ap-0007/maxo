from unihttp.http import HTTPRequest, HTTPResponse
from unihttp.middlewares import AsyncHandler

from maxo.backoff import Backoff, BackoffConfig
from maxo.errors.api import MaxBotBadRequestError

# Код и маркер сообщения ошибки "файл ещё не обработан сервером"
NOT_READY_CODE = "attachment.not.ready"
NOT_READY_MESSAGE_MARK = "not.processed"

# Значения подобраны эмпирически (см. examples/research_upload_delay.py):
# после начального умного сна остаётся небольшой "хвост",
# который добираем частыми короткими ретраями
DEFAULT_NOT_READY_BACKOFF = BackoffConfig(
    min_delay=0.2,
    max_delay=3.0,
    factor=1.6,
    jitter=0.1,
)
DEFAULT_MAX_RETRIES = 10


def is_attachment_not_ready(error: MaxBotBadRequestError) -> bool:
    """Проверяет, что ошибка означает "вложение ещё обрабатывается сервером"."""
    code = error.code or ""
    message = error.message or ""
    return code == NOT_READY_CODE or NOT_READY_MESSAGE_MARK in message


class AttachmentNotReadyRetryMiddleware:
    """
    Ретраит запрос, если MAX ответил `attachment.not.ready`.

    Структурно реализует `unihttp.middlewares.AsyncMiddleware`
    (без явного наследования Protocol, чтобы работал `__slots__`).

    MAX отдаёт эту ошибку, когда файл ещё не дообработан после загрузки.
    В остальных случаях ошибки пробрасываются как есть - ретраятся только
    "не готов", но не, например, "должно быть одно вложение".

    Повторы идут с экспоненциальным backoff (`maxo.backoff.Backoff`),
    пока файл не будет готов или не исчерпается `max_retries`.
    """

    __slots__ = ("_backoff_config", "_max_retries")

    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_config: BackoffConfig | None = None,
    ) -> None:
        self._max_retries = max_retries
        self._backoff_config = backoff_config or DEFAULT_NOT_READY_BACKOFF

    async def handle(
        self,
        request: HTTPRequest,
        next_handler: AsyncHandler,
    ) -> HTTPResponse:
        backoff = Backoff(self._backoff_config)

        while True:
            try:
                return await next_handler(request)
            except MaxBotBadRequestError as error:
                if (
                    not is_attachment_not_ready(error)
                    or backoff.counter >= self._max_retries
                ):
                    raise
                backoff.next()
                await backoff.sleep()
