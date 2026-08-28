from unihttp.http import HTTPResponse
from unihttp.method import BaseMethod

from maxo import loggers
from maxo.types.base import MaxoType


class MaxoMethod[MethodResultT](BaseMethod[MethodResultT], MaxoType):
    """
    Базовый метод для методов Bot API Max.
    """

    def validate_response(self, response: HTTPResponse) -> None:
        loggers.methods.debug("Raw response: %s", response.data)
