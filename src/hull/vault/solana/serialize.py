"""
Serialization and compression utilities for on-chain storage
"""

import hashlib
import json
from typing import Any

import msgpack

from ...pilot.maneuver import Maneuver


def compress_action(maneuver: Maneuver | dict[str, Any]) -> bytes:
    """
    Compress maneuver for efficient storage

    Args:
        maneuver: Maneuver dict (with 'type' field)

    Returns:
        Compressed bytes

    Example:
        from hull.pilot.maneuver import maneuver
        a = maneuver('click', x=100, y=200)
        compressed = compress_action(a)
        # Store compressed data on-chain
    """
    # Maneuver is now a TypedDict, which is just a dict at runtime
    return msgpack.packb(maneuver, use_bin_type=True)


def decompress_action(data: bytes) -> dict[str, Any]:
    """
    Decompress maneuver data

    Args:
        data: Compressed bytes

    Returns:
        Maneuver dictionary

    Example:
        action_dict = decompress_action(compressed_data)
        # action_dict is ready to use as an Maneuver
    """
    return msgpack.unpackb(data, raw=False)


def hash_action(maneuver: Maneuver | dict[str, Any]) -> str:
    """
    Create hash of maneuver for verification

    Args:
        maneuver: Maneuver to hash

    Returns:
        Hex string hash

    Example:
        from hull.pilot.maneuver import maneuver
        a = maneuver('click', x=100, y=200)
        action_hash = hash_action(a)
        # Store hash on-chain for verification
    """
    # Maneuver is now a TypedDict, which is just a dict at runtime
    # Ensure consistent ordering
    json_str = json.dumps(maneuver, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


def merkle_root(actions: list[Maneuver | dict[str, Any]]) -> str:
    """
    Calculate merkle root of maneuver list

    Args:
        actions: List of actions

    Returns:
        Merkle root hash

    Example:
        root = merkle_root(episode.actions)
        # Store root on-chain for batch verification
    """
    if not actions:
        return hashlib.sha256(b"").hexdigest()

    # Get leaf hashes
    hashes = [hash_action(maneuver) for maneuver in actions]

    # Build merkle tree
    while len(hashes) > 1:
        # Pad with last hash if odd number
        if len(hashes) % 2 == 1:
            hashes.append(hashes[-1])

        # Combine pairs
        new_hashes = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            new_hash = hashlib.sha256(combined.encode()).hexdigest()
            new_hashes.append(new_hash)

        hashes = new_hashes

    return hashes[0]


def compress_state(state: dict[str, Any], include_visual: bool = False) -> bytes:
    """
    Compress state for storage

    Args:
        state: State dictionary
        include_visual: Whether to include visual data

    Returns:
        Compressed bytes

    Example:
        compressed = compress_state(state_dict)
        # Store compressed state reference
    """
    data = {
        "timestamp": state.get("timestamp"),
        "metadata": state.get("metadata", {}),
    }

    if include_visual and "visual" in state:
        # Visual data is typically too large for on-chain
        # Store hash reference instead
        visual_hash = hashlib.sha256(state["visual"]).hexdigest()
        data["visual_hash"] = visual_hash

    return msgpack.packb(data, use_bin_type=True)


def create_action_proof(
    maneuver: Maneuver | dict[str, Any],
    state_before: dict[str, Any],
    state_after: dict[str, Any],
) -> dict[str, str]:
    """
    Create cryptographic proof of maneuver execution

    Args:
        maneuver: Maneuver that was executed
        state_before: State before maneuver
        state_after: State after maneuver

    Returns:
        Proof dictionary with hashes

    Example:
        proof = create_action_proof(maneuver, state1, state2)
        # Store proof on-chain for verification
    """
    return {
        "action_hash": hash_action(maneuver),
        "state_before_hash": hashlib.sha256(
            json.dumps(state_before, sort_keys=True).encode()
        ).hexdigest(),
        "state_after_hash": hashlib.sha256(
            json.dumps(state_after, sort_keys=True).encode()
        ).hexdigest(),
        "combined_hash": hashlib.sha256(
            (
                hash_action(maneuver)
                + hashlib.sha256(
                    json.dumps(state_before, sort_keys=True).encode()
                ).hexdigest()
                + hashlib.sha256(
                    json.dumps(state_after, sort_keys=True).encode()
                ).hexdigest()
            ).encode()
        ).hexdigest(),
    }


def estimate_storage_size(actions: list[dict[str, Any]]) -> int:
    """
    Estimate on-chain storage size

    Args:
        actions: List of actions

    Returns:
        Estimated bytes

    Example:
        size = estimate_storage_size(batch)
        cost = estimate_cost(size)
    """
    compressed = msgpack.packb(actions, use_bin_type=True)
    return len(compressed)
