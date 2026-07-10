from json import JSONDecodeError
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.pytest_plugin import AiohttpClient
from aiohttp.web_app import Application

from maxo.transport.webhook.adapters.aiohttp.adapter import (
    AiohttpBoundRequest,
    AiohttpWebAdapter,
)


@pytest.fixture
def aiohttp_app() -> web.Application:
    return web.Application()


@pytest.fixture
def mocked_engine() -> MagicMock:
    engine = MagicMock()
    engine.feed_request = AsyncMock()
    return engine


async def test_adapter(aiohttp_client: AiohttpClient, aiohttp_app: Application) -> None:
    payload = None

    async def handler(request: AiohttpBoundRequest) -> web.Response:
        nonlocal payload

        assert isinstance(request, AiohttpBoundRequest)
        payload = await request.json()
        return web.Response(status=200)

    engine = AsyncMock(side_effect=handler)

    adapter = AiohttpWebAdapter()
    adapter.register(aiohttp_app, "/webhook", engine)

    client = await aiohttp_client(aiohttp_app)
    response = await client.post("/webhook", json={"foo": "bar"})
    assert response.status == 200
    await response.read()

    engine.assert_awaited_once()
    request = engine.call_args.args[0]
    assert isinstance(request, AiohttpBoundRequest)
    assert payload == {"foo": "bar"}


async def test_bound_request_properties(
    aiohttp_client: AiohttpClient,
    aiohttp_app: Application,
) -> None:
    captured: dict[str, Any] = {}

    async def handler(request: AiohttpBoundRequest) -> web.Response:
        captured["headers"] = request.headers.get("X-Test")
        captured["query"] = request.query_params.get("q")
        captured["path_params"] = dict(request.path_params)
        captured["client_ip"] = request.client_ip
        return web.Response(status=200)

    adapter = AiohttpWebAdapter()
    adapter.register(aiohttp_app, "/webhook/{token}", handler)  # type: ignore[arg-type]

    client = await aiohttp_client(aiohttp_app)
    response = await client.post(
        "/webhook/abc?q=1",
        json={},
        headers={"X-Test": "value"},
    )

    assert response.status == 200
    assert captured["headers"] == "value"
    assert captured["query"] == "1"
    assert captured["path_params"] == {"token": "abc"}
    assert captured["client_ip"] is not None


async def test_json_raises_decode_error_on_wrong_content_type(
    aiohttp_client: AiohttpClient,
    aiohttp_app: Application,
) -> None:
    errors: list[Exception] = []

    async def handler(request: AiohttpBoundRequest) -> web.Response:
        try:
            await request.json()
        except JSONDecodeError as e:
            errors.append(e)
        return web.Response(status=200)

    adapter = AiohttpWebAdapter()
    adapter.register(aiohttp_app, "/webhook", handler)  # type: ignore[arg-type]

    client = await aiohttp_client(aiohttp_app)
    await (await client.post("/webhook", data=b"raw")).read()

    assert errors


def test_client_ip_is_none_without_peername() -> None:
    request = MagicMock()
    request.transport.get_extra_info.return_value = None

    assert AiohttpBoundRequest(request).client_ip is None


async def test_register_hooks(aiohttp_app: Application) -> None:
    startup = AsyncMock()
    shutdown = AsyncMock()

    AiohttpWebAdapter().register(
        aiohttp_app,
        "/webhook",
        AsyncMock(),
        on_startup=startup,
        on_shutdown=shutdown,
    )

    assert startup in aiohttp_app.on_startup
    assert shutdown in aiohttp_app.on_shutdown


def test_create_json_response() -> None:
    response = AiohttpWebAdapter().create_json_response(201, {"ok": True})

    assert response.status == 201
