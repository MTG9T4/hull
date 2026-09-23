"""
Core maneuver system
Simple, composable, and extensible
"""

from types import SimpleNamespace
from typing import Protocol


class Maneuver(Protocol):
    type: str


def maneuver(type: str, **parms) -> Maneuver:
    return SimpleNamespace(type=type, **parms)


def chain(*actions: Maneuver) -> list[Maneuver]:
    """Chain actions together"""
    return list(actions)


def batch(*actions: Maneuver) -> Maneuver:
    """Batch actions for parallel execution"""
    return maneuver("batch", actions=list(actions))


def sequence(*actions: Maneuver, delay: float = 0) -> Maneuver:
    """Create sequence with optional delay between actions"""
    return maneuver("sequence", actions=list(actions), delay=delay)


def pipe(*funcs):
    """Pipe functions together"""

    def piped(initial):
        result = initial
        for f in funcs:
            result = f(result)
        return result

    return piped


def compose(*funcs):
    """Compose functions right-to-left"""
    return pipe(*reversed(funcs))


# Generic actions
def wait(duration: float) -> Maneuver:
    """Wait for specified duration"""
    return maneuver("wait", duration=duration)


def capture() -> Maneuver:
    """Capture current state"""
    return maneuver("capture")


def record(start: bool = True) -> Maneuver:
    """Start or stop recording"""
    return maneuver("record", start=start)


def parallel(*actions: Maneuver) -> Maneuver:
    """Execute actions in parallel"""
    return maneuver("parallel", actions=list(actions))


def retry(a: Maneuver, attempts: int = 3, delay: float = 1.0) -> Maneuver:
    """Retry an maneuver with backoff"""
    return maneuver("retry", maneuver=a, attempts=attempts, delay=delay)


def throttle(a: Maneuver, rate: float) -> Maneuver:
    """Throttle maneuver execution rate"""
    return maneuver("throttle", maneuver=a, rate=rate)


def debounce(a: Maneuver, delay: float) -> Maneuver:
    """Debounce maneuver execution"""
    return maneuver("debounce", maneuver=a, delay=delay)
