from unihttp.method import BaseMethod

from maxo.types.base import MaxoType


class MaxoMethod[MethodResultT](BaseMethod[MethodResultT], MaxoType):
    """
    Базовый метод для методов Bot API Max.
    """
