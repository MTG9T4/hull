"""
Base bridge interface
"""

from abc import ABC, abstractmethod

from ..pilot.types import State


class BaseBridge(ABC):
    """Abstract base class for all bridges."""

    @abstractmethod
    async def get_state(self) -> State:
        """Get current state"""
        pass

    @abstractmethod
    async def execute_maneuver(self, action_type: str, **params) -> bool:
        """Execute environment-specific maneuver"""
        pass
