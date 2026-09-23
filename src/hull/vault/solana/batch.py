"""
Maneuver batching utilities for efficient on-chain recording
"""

import time
from dataclasses import dataclass
from typing import Any

import msgpack


@dataclass
class SolanaBatchConfig:
    """Configuration for maneuver batching."""

    max_size: int = 20  # Max actions per batch
    max_bytes: int = 1000  # Max bytes per batch
    timeout: float = 5.0  # Flush after N seconds
    compression: str = "msgpack"  # Compression method


class SolanaBatch:
    """Batch maneuvers for efficient on-chain settlement.
    
    Example:
        batch = SolanaBatch()
        batch.add(maneuver("click", x=100, y=200))
        await batch.submit()"""

    def __init__(
        self,
        max_size: int = 20,
        max_bytes: int = 1000,
        timeout: float = 5.0,
        compression: str = "msgpack",
    ):
        """
        Initialize batch with config

        Args:
            max_size: Max actions per batch
            max_bytes: Max bytes per batch
            timeout: Flush after N seconds
            compression: Compression method (msgpack, json, none)
        """
        self.config = SolanaBatchConfig(
            max_size=max_size,
            max_bytes=max_bytes,
            timeout=timeout,
            compression=compression,
        )
        self.actions: list[dict[str, Any]] = []
        self.start_time: float | None = None
        self.total_bytes: int = 0

    def add(self, maneuver: dict[str, Any]) -> None:
        """
        Add maneuver to batch

        Args:
            maneuver: Maneuver dictionary to add
        """
        if not self.start_time:
            self.start_time = time.time()

        # Estimate size
        action_bytes = len(msgpack.packb(maneuver))

        # Check if adding would exceed limits
        if self.actions and (self.total_bytes + action_bytes > self.config.max_bytes):
            # Don't add, let caller flush first
            return

        self.actions.append(maneuver)
        self.total_bytes += action_bytes

    def should_flush(self) -> bool:
        """
        Check if batch should be flushed

        Returns:
            True if batch should be flushed
        """
        if not self.actions:
            return False

        # Size limit
        if len(self.actions) >= self.config.max_size:
            return True

        # Byte limit
        if self.total_bytes >= self.config.max_bytes:
            return True

        # Time limit
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed >= self.config.timeout:
                return True

        return False

    def flush(self) -> list[dict[str, Any]]:
        """
        Flush and return all actions

        Returns:
            List of actions
        """
        actions = self.actions.copy()
        self.actions = []
        self.start_time = None
        self.total_bytes = 0
        return actions

    def compress(self) -> bytes:
        """
        Compress current batch

        Returns:
            Compressed bytes
        """
        if not self.actions:
            return b""

        if self.config.compression == "msgpack":
            return msgpack.packb(self.actions)
        elif self.config.compression == "json":
            import json

            return json.dumps(self.actions).encode()
        else:
            # No compression
            return str(self.actions).encode()

    def size(self) -> int:
        """Get current batch size"""
        return len(self.actions)

    def is_empty(self) -> bool:
        """Check if batch is empty"""
        return len(self.actions) == 0

    def clear(self) -> None:
        """Clear batch without returning actions"""
        self.actions = []
        self.start_time = None
        self.total_bytes = 0

    def get_stats(self) -> dict[str, Any]:
        """
        Get batch statistics

        Returns:
            Dict with batch stats
        """
        elapsed = 0.0
        if self.start_time:
            elapsed = time.time() - self.start_time

        return {
            "size": len(self.actions),
            "bytes": self.total_bytes,
            "elapsed": elapsed,
            "compression": self.config.compression,
        }


def create_batch_manager(configs: dict[str, SolanaBatchConfig]) -> dict[str, SolanaBatch]:
    """
    Create multiple named batches

    Args:
        configs: Dict of name -> SolanaBatchConfig

    Returns:
        Dict of name -> SolanaBatch

    Example:
        batches = create_batch_manager({
            "high_priority": SolanaBatchConfig(max_size=5, timeout=1.0),
            "low_priority": SolanaBatchConfig(max_size=50, timeout=30.0),
        })

        batches["high_priority"].add(critical_action)
        batches["low_priority"].add(normal_action)
    """
    return {name: SolanaBatch(**config.__dict__) for name, config in configs.items()}
