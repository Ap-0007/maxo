from dataclasses import dataclass

from unihttp.clients.base import BaseAsyncClient

from maxo.bot import UploadConfig
from maxo.bot.defaults import BotDefaults


@dataclass(slots=True)
class BotConfig:
    client: BaseAsyncClient

    defaults: BotDefaults | None = None
    upload_config: UploadConfig | None = None
    warming_up: bool = True
