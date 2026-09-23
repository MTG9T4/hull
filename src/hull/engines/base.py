"""
Base class for all algorithms
"""

from abc import ABC, abstractmethod
from typing import Any

from ..pilot.maneuver import Maneuver, maneuver
from ..pilot.types import State


class Algorithm(ABC):
    """Abstract base class for learning engines used by pilots."""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize algorithm

        Args:
            config: Algorithm configuration
        """
        self.config = config or {}
        self.is_trained = False
        self.metadata: dict[str, Any] = {}

    @abstractmethod
    async def predict(
        self, state: State, context: dict[str, Any] | None = None
    ) -> Maneuver:
        """
        Predict next maneuver given current state

        Args:
            state: Current state
            context: Additional context

        Returns:
            Predicted maneuver
        """
        pass

    @abstractmethod
    async def train(
        self,
        data: list[dict[str, Any]],
        validation_data: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Train the algorithm on data

        Args:
            data: Training data
            validation_data: Optional validation data

        Returns:
            Training metrics
        """
        pass

    @abstractmethod
    def save(self, path: str):
        """Save algorithm state to disk"""
        pass

    @abstractmethod
    def load(self, path: str):
        """Load algorithm state from disk"""
        pass

    def preprocess_state(self, state: State) -> Any:
        """
        Preprocess state for algorithm input

        Args:
            state: Raw state

        Returns:
            Preprocessed state
        """
        # Default: return state as-is
        return state

    def postprocess_action(self, action_obj: Any) -> Maneuver:
        """
        Postprocess algorithm output to maneuver

        Args:
            action_obj: Raw algorithm output

        Returns:
            Maneuver object
        """
        # Default: assume maneuver is already an Maneuver object
        if isinstance(action_obj, dict) and "type" in action_obj:
            # Convert dict to proper Maneuver using maneuver factory
            action_type = action_obj.get("type", "unknown")
            params = {k: v for k, v in action_obj.items() if k != "type"}
            return maneuver(action_type, **params)

        # Try to convert dict to Maneuver using maneuver factory
        if isinstance(action_obj, dict):
            action_type = action_obj.get("type", "unknown")
            params = {k: v for k, v in action_obj.items() if k != "type"}
            return maneuver(action_type, **params)

        raise ValueError(f"Cannot convert {type(action_obj)} to Maneuver")

    def get_info(self) -> dict[str, Any]:
        """Get algorithm information"""
        return {
            "class": self.__class__.__name__,
            "config": self.config,
            "is_trained": self.is_trained,
            "metadata": self.metadata,
        }
