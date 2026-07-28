from dataclasses import dataclass

from unihttp.markers import Body

from maxo.omit import Omittable, Omitted


@dataclass(frozen=True, slots=True)
class WebhookConfig:
    """Webhook configuration for setWebhook API parameters."""

    update_types: Body[Omittable[list[str]]] = Omitted()  # noqa: RUF009
