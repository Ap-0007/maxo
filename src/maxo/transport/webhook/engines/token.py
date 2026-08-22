from typing import Any, Generic

from maxo import Bot, Dispatcher
from maxo.errors import MaxBotApiError
from maxo.loggers import webhook
from maxo.transport.webhook.configs.bot import BotConfig
from maxo.transport.webhook.configs.webhook import WebhookConfig
from maxo.transport.webhook.engines.base import AppT, FrameworkResponseT, RawRequestT
from maxo.transport.webhook.engines.multi import BaseMultiBotEngine
from maxo.transport.webhook.route import Route
from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.security import Security
from maxo.transport.webhook.web.base import WebAdapter


class TokenEngine(
    BaseMultiBotEngine[AppT, RawRequestT, FrameworkResponseT],
    Generic[AppT, RawRequestT, FrameworkResponseT],
):
    """
    Multi-bot webhook engine that resolves the bot from a `{bot_token}` route param.

    E.g. `Route(path="/webhook/{bot_token}", params={"bot_token": BotTokenParam()})`.
    """

    def __init__(
        self,
        dispatcher: Dispatcher,
        web: WebAdapter[AppT, RawRequestT, FrameworkResponseT],
        route: Route,
        bot_config: BotConfig,
        security: Security | None = None,
        webhook_config: WebhookConfig | None = None,
        shutdown_timeout: float = 10.0,
    ) -> None:
        super().__init__(
            dispatcher=dispatcher,
            web=web,
            route=route,
            security=security,
            webhook_config=webhook_config,
            shutdown_timeout=shutdown_timeout,
        )
        self.bot_config = bot_config
        self._token_ids: dict[str, int] = {}

    async def add_bot(
        self,
        token: str,
        webhook_config: WebhookConfig | None = None,
    ) -> Bot:
        bot = self._build_bot(token)
        await bot.get_my_info()

        kwargs = await self._build_webhook_kwargs(
            bot=bot,
            base_config=webhook_config or self.webhook_config,
        )
        await bot.subscribe(url=await self.route.build_url(bot=bot), **kwargs)

        if (existing := self._bots.get(bot.info.id)) is not None:
            # URL contains the token: same token = same URL, already subscribed
            await self.remove_bot(bot.info.id, unsubscribe=existing.token != token)

        self._bots[bot.info.id] = bot
        self._token_ids[token] = bot.info.id

        webhook.info("Added bot %s to token engine and set webhook", bot.info.id)
        return bot

    async def remove_bot(self, bot_id: int, unsubscribe: bool = True) -> bool:
        bot = self._bots.pop(bot_id, None)
        if bot is None:
            return False

        self._token_ids.pop(bot.token, None)

        try:
            if unsubscribe:
                await bot.unsubscribe(url=await self.route.build_url(bot=bot))
        finally:
            if (tracker := self._task_trackers.pop(bot_id, None)) is not None:
                await tracker.close(timeout=self.shutdown_timeout)
            await bot.close()

        webhook.info("Removed bot %s from token engine", bot_id)
        return True

    async def _resolve_bot(self, route_params: RouteParams) -> Bot | None:
        token = route_params.get("bot_token")
        if not isinstance(token, str) or not token:
            return None

        if (bot_id := self._token_ids.get(token)) is not None:
            return self._bots.get(bot_id)

        bot = self._build_bot(token)
        try:
            await bot.get_my_info()
        except MaxBotApiError:
            return None

        existing = self._bots.get(bot.info.id)
        if existing is not None and existing.token == token:
            self._token_ids[token] = existing.info.id
            return existing

        if existing is not None:
            self._token_ids.pop(existing.token, None)

        self._bots[bot.info.id] = bot
        self._token_ids[token] = bot.info.id
        return bot

    async def _on_shutdown(self, app: AppT, *args: Any, **kwargs: Any) -> None:
        await super()._on_shutdown(app, *args, **kwargs)
        self._token_ids.clear()

    def _build_bot(self, token: str) -> Bot:
        return Bot(
            token=token,
            client=self.bot_config.client,
            defaults=self.bot_config.defaults,
            upload_config=self.bot_config.upload_config,
            warming_up=self.bot_config.warming_up,
        )
