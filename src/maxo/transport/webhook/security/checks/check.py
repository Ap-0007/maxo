from typing import Protocol

from maxo.transport.webhook.engines.target import Target
from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.web.base import WebRequest


class SecurityCheck(Protocol):
    """Protocol for security check on webhook requests."""

    async def verify(
        self,
        target: Target,
        request: WebRequest,
        route_params: RouteParams,
    ) -> bool:
        """
        Perform a security check on the incoming webhook request.

        :param target: The target bot that received the request.
        :param request: The webhook request to verify.
        :param route_params: Route parameters mapping for the request.
        :return: True if the check passes (allow the request), False otherwise (reject).
        """
        raise NotImplementedError
