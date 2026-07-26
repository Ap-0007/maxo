from maxo.transport.webhook.engines.target import Target
from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.security.checks.check import SecurityCheck
from maxo.transport.webhook.web.base import WebRequest


class RecordingCheck(SecurityCheck):
    def __init__(self, name: str, *, result: bool, calls: list[str]) -> None:
        self.name = name
        self.result = result
        self.calls = calls

    async def verify(
        self,
        target: Target,
        request: WebRequest,
        route_params: RouteParams,
    ) -> bool:
        self.calls.append(self.name)
        return self.result
