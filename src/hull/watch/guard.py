"""
Safety guard for maneuver validation and recovery
"""

from collections.abc import Callable

from ..pilot.maneuver import Maneuver
from ..pilot.types import State


class Sentry:
    """Safety sentry for any bridge type. Validates maneuvers before they run."""

    def __init__(self):
        self.precondition_rules = {}
        self.postcondition_rules = {}
        self.recovery_strategies = {}
        self.global_rules = []

    async def check_preconditions(self, maneuver: Maneuver, state: State) -> bool:
        """Check if maneuver is safe to execute"""
        # Check global rules first
        for rule in self.global_rules:
            if not await rule(maneuver, state):
                return False

        # Check maneuver-specific preconditions
        if maneuver.type in self.precondition_rules:
            for rule in self.precondition_rules[maneuver.type]:
                if not await rule(maneuver, state):
                    return False

        return True

    async def check_postconditions(
        self, maneuver: Maneuver, state_before: State, state_after: State
    ) -> bool:
        """Verify maneuver had expected effect"""
        # Check maneuver-specific postconditions
        if maneuver.type in self.postcondition_rules:
            for rule in self.postcondition_rules[maneuver.type]:
                if not await rule(maneuver, state_before, state_after):
                    return False

        return True

    async def rollback(self, maneuver: Maneuver, state: State) -> bool:
        """Attempt to rollback failed maneuver"""
        if maneuver.type in self.recovery_strategies:
            strategy = self.recovery_strategies[maneuver.type]
            return await strategy(maneuver, state)

        return False

    def add_global_rule(self, rule: Callable):
        """Add rule that applies to all actions"""
        self.global_rules.append(rule)

    def add_precondition(self, action_type: str, rule: Callable):
        """Add precondition rule for specific maneuver type"""
        if action_type not in self.precondition_rules:
            self.precondition_rules[action_type] = []
        self.precondition_rules[action_type].append(rule)

    def add_postcondition(self, action_type: str, rule: Callable):
        """Add postcondition rule for specific maneuver type"""
        if action_type not in self.postcondition_rules:
            self.postcondition_rules[action_type] = []
        self.postcondition_rules[action_type].append(rule)

    def add_recovery_strategy(self, action_type: str, strategy: Callable):
        """Add recovery strategy for maneuver type"""
        self.recovery_strategies[action_type] = strategy
