from typing import cast

import pytest

from maxo.bot.api_client import MaxApiClient
from maxo.bot.state import (
    ClosedBotState,
    ConnectingBotState,
    EmptyBotState,
    RunningBotState,
)
from maxo.errors.state import StateError
from tests.factories import make_bot_info


def make_api_client() -> MaxApiClient:
    return cast(MaxApiClient, object())


def test_empty_bot_state() -> None:
    state = EmptyBotState()

    assert state.started is False
    assert state.closed is False
    with pytest.raises(StateError, match="Not started bot"):
        _ = state.api_client
    with pytest.raises(StateError, match="Not started bot"):
        _ = state.info


def test_closed_bot_state() -> None:
    state = ClosedBotState()

    assert state.started is False
    assert state.closed is True
    with pytest.raises(StateError, match="Bot closed"):
        _ = state.api_client
    with pytest.raises(StateError, match="Bot closed"):
        _ = state.info


def test_connecting_bot_state() -> None:
    api_client = make_api_client()
    state = ConnectingBotState(api_client=api_client)

    assert state.started is True
    assert state.closed is False
    assert state.api_client is api_client
    with pytest.raises(StateError, match="Bot is connecting"):
        _ = state.info


def test_running_bot_state() -> None:
    api_client = make_api_client()
    info = make_bot_info()
    state = RunningBotState(info=info, api_client=api_client)

    assert state.started is True
    assert state.closed is False
    assert state.api_client is api_client
    assert state.info is info
