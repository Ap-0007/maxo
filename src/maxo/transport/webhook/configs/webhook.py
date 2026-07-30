from dataclasses import dataclass

from maxo.omit import Omittable, Omitted


@dataclass(frozen=True, slots=True)
class WebhookConfig:
    """Webhook configuration for setWebhook API parameters."""

    update_types: Omittable[list[str]] = Omitted()  # noqa: RUF009
