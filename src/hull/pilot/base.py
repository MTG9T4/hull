"""
Base pilot class
"""

import asyncio
import logging
from typing import Any

from ..bridge.base import BaseBridge
from .types import State

logger = logging.getLogger(__name__)


class Pilot:
    """Autonomous pilot that acts through one or more bridges.

    Perceives state, chooses maneuvers, and executes them —
    self-healing, resource-managed, and hard to kill."""

    def __init__(self, bridges: dict[str, BaseBridge]):
        """
        Initialize pilot with one or more bridges

        Args:
            bridges: Dictionary of named bridges
                     e.g. {"desktop": DesktopBridge(), "robot": BrewieRobot()}
        """
        self.bridges = bridges
        self._states: dict[str, State] = {}

    def _resolve_bridge(self, bridge_name: str | None) -> tuple[str, BaseBridge]:
        """Pick a bridge by name, or the first available one."""
        if bridge_name:
            if bridge_name not in self.bridges:
                raise ValueError(f"Bridge '{bridge_name}' not found")
        else:
            # Use first bridge if not specified
            bridge_name = next(iter(self.bridges))
        return bridge_name, self.bridges[bridge_name]

    async def get_state(self, bridge_name: str | None = None) -> State:
        """Get state from specific bridge or first available"""
        bridge_name, bridge = self._resolve_bridge(bridge_name)
        state = await bridge.get_state()
        self._states[bridge_name] = state
        return state

    async def execute_maneuver(
        self,
        maneuver_type: str,
        bridge_name: str | None = None,
        *,
        retries: int = 0,
        timeout: float | None = None,
        backoff: float = 0.5,
        **params,
    ) -> bool:
        """Execute a maneuver on a bridge, with self-healing retries and timeout.

        Args:
            maneuver_type: Which maneuver to run (e.g. "click", "move").
            bridge_name: Target bridge, or the first one if omitted.
            retries: How many times to retry after a failure (0 = try once).
            timeout: Max seconds per attempt before it counts as failed.
            backoff: Base delay in seconds between retries (doubles each time).
            **params: Passed through to the bridge.

        Returns:
            True if the maneuver eventually succeeded, False otherwise.
            A failed maneuver never raises — the pilot absorbs the failure,
            logs it, and keeps sailing.
        """
        last_error = "unknown failure"
        attempts = max(0, retries) + 1
        # Resolve once up front: an unknown bridge is a programming error,
        # not a transient failure worth retrying.
        _, bridge = self._resolve_bridge(bridge_name)
        for attempt in range(1, attempts + 1):
            try:
                coro = bridge.execute_maneuver(maneuver_type, **params)
                ok = await asyncio.wait_for(coro, timeout) if timeout else await coro
                if ok:
                    if attempt > 1:
                        logger.info(
                            "Maneuver '%s' succeeded on attempt %d/%d",
                            maneuver_type,
                            attempt,
                            attempts,
                        )
                    return True
                last_error = "bridge reported failure"
            except asyncio.TimeoutError:
                last_error = f"timed out after {timeout}s"
            except Exception as exc:  # noqa: BLE001 - bridges fail in arbitrary ways
                last_error = f"{type(exc).__name__}: {exc}"

            if attempt < attempts:
                delay = backoff * (2 ** (attempt - 1))
                logger.warning(
                    "Maneuver '%s' failed (attempt %d/%d): %s — retrying in %.2fs",
                    maneuver_type,
                    attempt,
                    attempts,
                    last_error,
                    delay,
                )
                if delay > 0:
                    await asyncio.sleep(delay)

        logger.error(
            "Maneuver '%s' failed after %d attempt(s): %s",
            maneuver_type,
            attempts,
            last_error,
        )
        return False

    async def health_check(self) -> dict[str, str]:
        """Probe every bridge and report its health.

        Returns:
            Mapping of bridge name to "ok", or a short error description
            for bridges that failed to report state.
        """
        report: dict[str, str] = {}
        for name, bridge in self.bridges.items():
            try:
                await bridge.get_state()
                report[name] = "ok"
            except Exception as exc:  # noqa: BLE001 - any failure means unhealthy
                report[name] = f"{type(exc).__name__}: {exc}"
                logger.warning("Bridge '%s' failed health check: %s", name, report[name])
        return report

    async def run(self, task: dict[str, Any]) -> Any:
        """
        Run a task across bridges

        Task format:
        {
            "bridge": "desktop",  # optional, defaults to first
            "maneuver": "click",
            "params": {"x": 100, "y": 200},
            "retries": 2,     # optional, self-healing retries
            "timeout": 10.0,  # optional, seconds per attempt
        }
        """
        bridge_name = task.get("bridge")
        maneuver = task.get("maneuver")
        params = task.get("params", {})
        retries = task.get("retries", 0)
        timeout = task.get("timeout")

        if not maneuver or not isinstance(maneuver, str):
            raise ValueError("Task must have a valid 'maneuver' field of type str")

        # After the check above, maneuver is guaranteed to be str
        return await self.execute_maneuver(
            str(maneuver), bridge_name, retries=retries, timeout=timeout, **params
        )

    def add_bridge(self, name: str, bridge: BaseBridge):
        """Add a new bridge"""
        self.bridges[name] = bridge

    def remove_bridge(self, name: str):
        """Remove a bridge"""
        if name in self.bridges:
            del self.bridges[name]
            if name in self._states:
                del self._states[name]
