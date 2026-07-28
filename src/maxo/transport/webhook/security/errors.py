import logging

from maxo.transport.webhook.errors import MaxoWebhookError


class SecurityError(MaxoWebhookError):
    code = "security_error"
    status_code = 403
    public_detail = "Forbidden"
    log_level = logging.WARNING


class SecretTokenError(SecurityError):
    code = "security_secret_token_invalid"
    status_code = 403
    public_detail = "Forbidden"
    log_level = logging.ERROR

    def __str__(self) -> str:
        return "Webhook security verification failed: invalid Telegram secret token."


class SecurityCheckError(SecurityError):
    code = "security_check_failed"
    status_code = 403
    public_detail = "Forbidden"
    log_level = logging.ERROR

    security_check: str
    client_ip: str | None = None

    def __str__(self) -> str:
        message = (
            f"Webhook security verification failed: security check rejected "
            f"request. Check: {self.security_check!r}."
        )

        if self.client_ip is not None:
            message += f" Client IP: {self.client_ip}"

        return message
