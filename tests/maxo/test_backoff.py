import pytest

from maxo.backoff import Backoff, BackoffConfig

BACKOFF_CONFIG = BackoffConfig(min_delay=0.1, max_delay=1.0, factor=2.0, jitter=0.0)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        (
            {"min_delay": 1.0, "max_delay": 1.0, "factor": 2.0, "jitter": 0.1},
            "`max_delay` should be greater than `min_delay`",
        ),
        (
            {"min_delay": 1.0, "max_delay": 1.0, "factor": 1.0, "jitter": 0.1},
            "`max_delay` should be greater than `min_delay`",
        ),
        (
            {"min_delay": 1.0, "max_delay": 2.0, "factor": 0.5, "jitter": 0.1},
            "`factor` should be greater than 1",
        ),
        (
            {"min_delay": 2.0, "max_delay": 1.0, "factor": 2.0, "jitter": 0.1},
            "`max_delay` should be greater than `min_delay`",
        ),
    ],
)
def test_backoff_config_rejects_invalid_values(
    kwargs: dict[str, float],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        BackoffConfig(**kwargs)


def test_backoff_config_accepts_valid_values() -> None:
    config = BackoffConfig(min_delay=1.0, max_delay=2.0, factor=1.2, jitter=0.1)

    assert config.min_delay == 1.0
    assert config.max_delay == 2.0
    assert config.factor == 1.2
    assert config.jitter == 0.1


def test_backoff_aliases() -> None:
    backoff = Backoff(config=BACKOFF_CONFIG)

    assert backoff.min_delay == BACKOFF_CONFIG.min_delay
    assert backoff.max_delay == BACKOFF_CONFIG.max_delay
    assert backoff.factor == BACKOFF_CONFIG.factor
    assert backoff.jitter == BACKOFF_CONFIG.jitter


def test_backoff_calculation_and_reset() -> None:
    backoff = Backoff(config=BACKOFF_CONFIG)

    assert backoff.current_delay == 0.0
    assert backoff.next_delay == 0.1

    delays: list[float] = []
    while backoff.next_delay < 1.0:
        backoff.next()
        delays.append(backoff.current_delay)

    assert delays == [0.1, 0.2, 0.4, 0.8]

    backoff.next()
    assert backoff.current_delay == 1.0
    assert backoff.next_delay == 1.0
    assert backoff.counter == 5
    assert repr(backoff) == "Backoff(tryings=5, current_delay=1.0, next_delay=1.0)"

    backoff.reset()
    assert backoff.current_delay == 0.0
    assert backoff.next_delay == 0.1
    assert backoff.counter == 0


async def test_backoff_sleep_uses_current_delay() -> None:
    backoff = Backoff(config=BACKOFF_CONFIG)

    await backoff.sleep()

    assert backoff.counter == 0
