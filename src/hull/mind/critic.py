"""
Lookout module for evaluating actions and providing feedback
"""

from typing import Any

from ..pilot.maneuver import Maneuver, maneuver
from ..pilot.types import State


class Lookout:
    """Watches maneuvers and their outcomes, feeding critique back to the pilot.
    Actor-lookout feedback for sharper behavior."""

    def __init__(self, model_provider: str | None = None):
        self.model_provider = model_provider
        self.evaluation_history: list[dict[str, Any]] = []

    async def evaluate_action(
        self,
        maneuver: Maneuver,
        state_before: State,
        state_after: State,
        goal: str | None = None,
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Evaluate if an maneuver was successful and provide feedback

        Returns:
            - success: Whether the maneuver achieved its intended effect
            - reason: Explanation of the evaluation
            - suggestions: Dict with improvement suggestions
        """
        evaluation: dict[str, Any] = {
            "maneuver": maneuver,
            "state_change": self._analyze_state_change(state_before, state_after),
            "goal_alignment": self._check_goal_alignment(maneuver, goal)
            if goal
            else None,
        }

        # Determine success based on state change
        success = evaluation["state_change"]["changed"]

        # Generate reason
        if success:
            reason = "Maneuver executed successfully with observable state change"
        else:
            reason = "No observable state change detected"

        # Generate suggestions
        suggestions = self._generate_suggestions(evaluation)

        # Store in history
        self.evaluation_history.append(
            {
                "maneuver": maneuver,
                "success": success,
                "reason": reason,
                "suggestions": suggestions,
            }
        )

        return success, reason, suggestions

    async def critique_plan(
        self, plan: list[Maneuver], current_state: State, goal: str
    ) -> dict[str, Any]:
        """
        Critique a plan before execution

        Returns:
            Dict with critique including potential issues and improvements
        """
        critique: dict[str, Any] = {
            "feasibility": self._assess_feasibility(plan, current_state),
            "efficiency": self._assess_efficiency(plan),
            "risks": self._identify_risks(plan),
            "improvements": [],
        }

        # Generate improvement suggestions
        if not critique["feasibility"]["is_feasible"]:
            critique["improvements"].append(
                {
                    "type": "feasibility",
                    "suggestion": "Revise plan to address feasibility issues",
                }
            )

        if critique["efficiency"]["score"] < 0.7:
            critique["improvements"].append(
                {
                    "type": "efficiency",
                    "suggestion": "Consider optimizing maneuver sequence",
                }
            )

        return critique

    async def suggest_correction(
        self, failed_action: Maneuver, error: str, state: State
    ) -> Maneuver | None:
        """
        Suggest a corrected maneuver after failure
        """
        # Analyze the failure
        failure_analysis = self._analyze_failure(failed_action, error, state)

        # Generate correction based on failure type
        if failure_analysis["type"] == "parameter_error":
            # Adjust parameters - cast Maneuver to dict to access params
            action_dict = dict(failed_action)  # type: ignore
            params = {k: v for k, v in action_dict.items() if k != "type"}
            corrected_params = self._adjust_parameters(
                params, failure_analysis["details"]
            )
            return maneuver(failed_action.type, **corrected_params)

        return None

    def _analyze_state_change(self, before: State, after: State) -> dict[str, Any]:
        """Analyze differences between states"""
        return {
            "changed": before != after,
            "timestamp_diff": after.timestamp - before.timestamp
            if after.timestamp and before.timestamp
            else 0,
        }

    def _check_goal_alignment(self, maneuver: Maneuver, goal: str) -> bool:
        """Check if maneuver aligns with goal"""
        # Simplified check - would use LLM in production
        return True

    def _generate_suggestions(self, evaluation: dict[str, Any]) -> dict[str, Any]:
        """Generate improvement suggestions based on evaluation"""
        suggestions = {}

        if not evaluation["state_change"]["changed"]:
            suggestions["retry"] = "Consider retrying with adjusted parameters"
            suggestions["alternative"] = "Try a different maneuver type"

        return suggestions

    def _assess_feasibility(self, plan: list[Maneuver], state: State) -> dict[str, Any]:
        """Assess if a plan is feasible given current state"""
        return {
            "is_feasible": True,  # Simplified
            "issues": [],
        }

    def _assess_efficiency(self, plan: list[Maneuver]) -> dict[str, Any]:
        """Assess plan efficiency"""
        return {
            "score": 0.8,  # Simplified scoring
            "redundant_actions": [],
        }

    def _identify_risks(self, plan: list[Maneuver]) -> list[dict[str, Any]]:
        """Identify potential risks in plan"""
        risks = []

        # Check for potentially destructive actions
        for act in plan:
            if act.type in ["delete", "remove", "clear"]:
                risks.append(
                    {"maneuver": act, "risk_type": "data_loss", "severity": "high"}
                )

        return risks

    def _analyze_failure(
        self, maneuver: Maneuver, error: str, state: State
    ) -> dict[str, Any]:
        """Analyze why an maneuver failed"""
        # Simplified analysis
        if "parameter" in error.lower():
            return {"type": "parameter_error", "details": {"error": error}}

        return {"type": "unknown", "details": {"error": error}}

    def _adjust_parameters(
        self, params: dict[str, Any], details: dict[str, Any]
    ) -> dict[str, Any]:
        """Adjust maneuver parameters based on failure analysis"""
        # Simplified adjustment
        adjusted = params.copy()

        # Example adjustments
        if "x" in adjusted and "y" in adjusted:
            # Slightly adjust coordinates
            adjusted["x"] = adjusted["x"] + 5
            adjusted["y"] = adjusted["y"] + 5

        return adjusted
