"""
Generic validator for maneuver parameters
"""

from typing import Any

from ..pilot.maneuver import Maneuver


class Validator:
    """Validates maneuver parameters and data"""

    def __init__(self):
        self.schemas = {}

    def register_schema(self, action_type: str, schema: dict[str, Any]):
        """Register validation schema for maneuver type"""
        self.schemas[action_type] = schema

    def validate_action(self, maneuver: Maneuver) -> tuple[bool, str | None]:
        """Validate maneuver parameters against schema"""
        if maneuver.type not in self.schemas:
            # No schema registered, allow by default
            return True, None

        schema = self.schemas[maneuver.type]

        # Cast Maneuver to dict to access params
        action_dict = dict(maneuver)  # type: ignore
        params = {k: v for k, v in action_dict.items() if k != "type"}

        # Check required parameters
        if "required" in schema:
            for param in schema["required"]:
                if param not in params:
                    return False, f"Missing required parameter: {param}"

        # Check parameter types
        if "types" in schema:
            for param, expected_type in schema["types"].items():
                if param in params:
                    if not isinstance(params[param], expected_type):
                        return (
                            False,
                            f"Parameter {param} must be of type {expected_type.__name__}",
                        )

        # Check parameter ranges/constraints
        if "constraints" in schema:
            for param, constraint in schema["constraints"].items():
                if param in params:
                    value = params[param]
                    if "min" in constraint and value < constraint["min"]:
                        return (
                            False,
                            f"Parameter {param} must be >= {constraint['min']}",
                        )
                    if "max" in constraint and value > constraint["max"]:
                        return (
                            False,
                            f"Parameter {param} must be <= {constraint['max']}",
                        )
                    if "enum" in constraint and value not in constraint["enum"]:
                        return (
                            False,
                            f"Parameter {param} must be one of {constraint['enum']}",
                        )

        return True, None

    def validate_data(
        self, data: Any, schema: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """Validate arbitrary data against schema"""
        # Generic data validation
        if "type" in schema:
            if not isinstance(data, schema["type"]):
                return False, f"Data must be of type {schema['type'].__name__}"

        if "properties" in schema and isinstance(data, dict):
            for prop, prop_schema in schema["properties"].items():
                if prop in data:
                    valid, error = self.validate_data(data[prop], prop_schema)
                    if not valid:
                        return False, f"Property {prop}: {error}"

        return True, None
