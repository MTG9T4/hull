"""
Base pilot class
"""

from typing import Any

from ..bridge.base import BaseBridge
from .types import State


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

    async def get_state(self, bridge_name: str | None = None) -> State:
        """Get state from specific bridge or first available"""
        if bridge_name:
            if bridge_name not in self.bridges:
                raise ValueError(f"Bridge '{bridge_name}' not found")
            bridge = self.bridges[bridge_name]
        else:
            # Use first bridge if not specified
            bridge_name = next(iter(self.bridges))
            bridge = self.bridges[bridge_name]

        state = await bridge.get_state()
        self._states[bridge_name] = state
        return state

    async def execute_maneuver(
        self, maneuver_type: str, bridge_name: str | None = None, **params
    ) -> bool:
        """Execute maneuver on specific bridge"""
        if bridge_name:
            if bridge_name not in self.bridges:
                raise ValueError(f"Bridge '{bridge_name}' not found")
            bridge = self.bridges[bridge_name]
        else:
            # Use first bridge if not specified
            bridge = next(iter(self.bridges.values()))

        return await bridge.execute_maneuver(maneuver_type, **params)

    async def run(self, task: dict[str, Any]) -> Any:
        """
        Run a task across bridges

        Task format:
        {
            "bridge": "desktop",  # optional, defaults to first
            "maneuver": "click",
            "params": {"x": 100, "y": 200}
        }
        """
        bridge_name = task.get("bridge")
        maneuver = task.get("maneuver")
        params = task.get("params", {})

        if not maneuver or not isinstance(maneuver, str):
            raise ValueError("Task must have a valid 'maneuver' field of type str")

        # After the check above, maneuver is guaranteed to be str
        return await self.execute_maneuver(str(maneuver), bridge_name, **params)

    def add_bridge(self, name: str, bridge: BaseBridge):
        """Add a new bridge"""
        self.bridges[name] = bridge

    def remove_bridge(self, name: str):
        """Remove a bridge"""
        if name in self.bridges:
            del self.bridges[name]
            if name in self._states:
                del self._states[name]
