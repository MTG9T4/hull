"""
Tests for Pilot self-healing execution: retries, timeouts, health checks.
"""

import asyncio

from ..bridge.base import BaseBridge
from .base import Pilot


class ScriptedBridge(BaseBridge):
    """Bridge that plays back a scripted sequence of outcomes.

    Each entry is either a bool (returned) or an Exception (raised).
    """

    def __init__(self, script, healthy=True):
        self.script = list(script)
        self.calls = 0
        self.healthy = healthy

    async def get_state(self):
        if not self.healthy:
            raise ConnectionError("bridge unreachable")
        return {"ok": True}

    async def execute_maneuver(self, maneuver_type, **params):
        self.calls += 1
        outcome = self.script.pop(0) if self.script else True
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class SlowBridge(BaseBridge):
    def __init__(self):
        self.calls = 0

    async def get_state(self):
        return {"ok": True}

    async def execute_maneuver(self, maneuver_type, **params):
        self.calls += 1
        await asyncio.sleep(10)
        return True


def test_execute_maneuver_success():
    pilot = Pilot({"stub": ScriptedBridge([True])})
    assert asyncio.run(pilot.execute_maneuver("click", x=1)) is True


def test_execute_maneuver_retries_on_exception_then_succeeds():
    bridge = ScriptedBridge([RuntimeError("boom"), True])
    pilot = Pilot({"stub": bridge})
    ok = asyncio.run(pilot.execute_maneuver("click", retries=2, backoff=0))
    assert ok is True
    assert bridge.calls == 2


def test_execute_maneuver_gives_up_after_retries():
    bridge = ScriptedBridge([RuntimeError("boom")] * 5)
    pilot = Pilot({"stub": bridge})
    ok = asyncio.run(pilot.execute_maneuver("click", retries=2, backoff=0))
    assert ok is False
    assert bridge.calls == 3  # initial attempt + 2 retries


def test_execute_maneuver_retries_on_false_result():
    bridge = ScriptedBridge([False, True])
    pilot = Pilot({"stub": bridge})
    ok = asyncio.run(pilot.execute_maneuver("click", retries=1, backoff=0))
    assert ok is True
    assert bridge.calls == 2


def test_execute_maneuver_timeout_counts_as_failure():
    bridge = SlowBridge()
    pilot = Pilot({"stub": bridge})
    ok = asyncio.run(pilot.execute_maneuver("click", timeout=0.05, backoff=0))
    assert ok is False
    assert bridge.calls == 1


def test_execute_maneuver_unknown_bridge_raises():
    pilot = Pilot({"stub": ScriptedBridge([True])})
    try:
        asyncio.run(pilot.execute_maneuver("click", bridge_name="nope"))
    except ValueError as exc:
        assert "nope" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_health_check_all_ok():
    pilot = Pilot({"a": ScriptedBridge([True]), "b": ScriptedBridge([True])})
    report = asyncio.run(pilot.health_check())
    assert report == {"a": "ok", "b": "ok"}


def test_health_check_reports_failure():
    pilot = Pilot({"good": ScriptedBridge([True]), "bad": ScriptedBridge([True], healthy=False)})
    report = asyncio.run(pilot.health_check())
    assert report["good"] == "ok"
    assert "ConnectionError" in report["bad"]


def test_run_task_with_retries_and_timeout():
    bridge = ScriptedBridge([RuntimeError("flaky"), True])
    pilot = Pilot({"stub": bridge})
    ok = asyncio.run(
        pilot.run(
            {
                "bridge": "stub",
                "maneuver": "click",
                "params": {"x": 5},
                "retries": 1,
                "timeout": 5.0,
            }
        )
    )
    assert ok is True
    assert bridge.calls == 2


def test_run_task_rejects_bad_maneuver():
    pilot = Pilot({"stub": ScriptedBridge([True])})
    try:
        asyncio.run(pilot.run({"bridge": "stub"}))
    except ValueError as exc:
        assert "maneuver" in str(exc)
    else:
        raise AssertionError("expected ValueError")
