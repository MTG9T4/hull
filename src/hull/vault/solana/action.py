"""
Solana-specific maneuver utilities
Functional utilities for compressing, hashing, and verifying actions on-chain
"""

import hashlib
import json
from typing import Any

import msgpack

from ...pilot.maneuver import Maneuver


def compress(maneuver: Maneuver | dict[str, Any]) -> bytes:
    """
    Compress maneuver for on-chain storage

    Args:
        maneuver: Maneuver to compress

    Returns:
        Compressed bytes

    Example:
        from hull.pilot.maneuver import maneuver
        from hull.vault.solana.maneuver import compress

        a = maneuver('click', x=100, y=200)
        compressed = compress(a)
    """
    return msgpack.packb(maneuver, use_bin_type=True)


def decompress(data: bytes) -> dict[str, Any]:
    """
    Decompress maneuver data from chain

    Args:
        data: Compressed bytes

    Returns:
        Maneuver dictionary

    Example:
        maneuver = decompress(compressed_data)
    """
    return msgpack.unpackb(data, raw=False)


def hash(maneuver: Maneuver | dict[str, Any]) -> str:
    """
    Create hash of maneuver for verification

    Args:
        maneuver: Maneuver to hash

    Returns:
        Hex string hash

    Example:
        from hull.pilot.maneuver import maneuver
        from hull.vault.solana.maneuver import hash

        a = maneuver('click', x=100, y=200)
        action_hash = hash(a)
    """
    json_str = json.dumps(maneuver, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


def merkle_root(actions: list[Maneuver | dict[str, Any]]) -> str:
    """
    Calculate merkle root for maneuver batch

    Args:
        actions: List of actions

    Returns:
        Merkle root hash

    Example:
        from hull.pilot.maneuver import chain, maneuver
        from hull.vault.solana.maneuver import merkle_root

        actions = chain(
            maneuver('click', x=100, y=200),
            maneuver('type', text='hello'),
            maneuver('wait', duration=1.0)
        )
        root = merkle_root(actions)
    """
    if not actions:
        return hashlib.sha256(b"").hexdigest()

    # Get leaf hashes
    hashes = [hash(maneuver) for maneuver in actions]

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


def proof(
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
        from hull.pilot.maneuver import maneuver
        from hull.vault.solana.maneuver import proof

        a = maneuver('click', x=100, y=200)
        p = proof(a, state_before, state_after)
    """
    action_hash = hash(maneuver)
    before_hash = hashlib.sha256(
        json.dumps(state_before, sort_keys=True).encode()
    ).hexdigest()
    after_hash = hashlib.sha256(
        json.dumps(state_after, sort_keys=True).encode()
    ).hexdigest()

    return {
        "maneuver": action_hash,
        "before": before_hash,
        "after": after_hash,
        "combined": hashlib.sha256(
            (action_hash + before_hash + after_hash).encode()
        ).hexdigest(),
    }


def size(actions: list[dict[str, Any]]) -> int:
    """
    Estimate storage size for actions

    Args:
        actions: List of actions

    Returns:
        Size in bytes

    Example:
        from hull.pilot.maneuver import chain, maneuver
        from hull.vault.solana.maneuver import size

        actions = chain(
            maneuver('click', x=100, y=200),
            maneuver('type', text='hello')
        )
        bytes_needed = size(actions)
    """
    compressed = msgpack.packb(actions, use_bin_type=True)
    return len(compressed)


def verify(maneuver: Maneuver | dict[str, Any], expected_hash: str) -> bool:
    """
    Verify maneuver against expected hash

    Args:
        maneuver: Maneuver to verify
        expected_hash: Expected hash value

    Returns:
        True if hash matches

    Example:
        from hull.vault.solana.maneuver import hash, verify

        a = maneuver('click', x=100, y=200)
        h = hash(a)

        # Later, verify
        is_valid = verify(a, h)
    """
    return hash(maneuver) == expected_hash


def batch_compress(actions: list[Maneuver | dict[str, Any]]) -> bytes:
    """
    Compress multiple actions as a batch

    Args:
        actions: List of actions

    Returns:
        Compressed batch

    Example:
        from hull.pilot.maneuver import chain, maneuver
        from hull.vault.solana.maneuver import batch_compress

        actions = chain(
            maneuver('click', x=100, y=200),
            maneuver('type', text='hello')
        )
        compressed = batch_compress(actions)
    """
    return msgpack.packb(actions, use_bin_type=True)


def batch_decompress(data: bytes) -> list[dict[str, Any]]:
    """
    Decompress batch of actions

    Args:
        data: Compressed batch data

    Returns:
        List of actions

    Example:
        actions = batch_decompress(compressed_data)
    """
    return msgpack.unpackb(data, raw=False)
