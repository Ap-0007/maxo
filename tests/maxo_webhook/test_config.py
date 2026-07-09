from maxo.bot.defaults import BotDefaults
from maxo.enums import TextFormat
from maxo.transport.webhook.config.bot import BotConfig


def test_bot_config_default_values() -> None:
    config = BotConfig()

    assert config.defaults is None


def test_bot_config_accepts_bot_defaults() -> None:
    defaults = BotDefaults(text_format=TextFormat.MARKDOWN)
    config = BotConfig(defaults=defaults)

    assert config.defaults is defaults
