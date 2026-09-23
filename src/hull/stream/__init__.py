"""Stream — capture, encode, and move video through the hull."""

from .fps import FPS
from .recorder import Recorder

__all__ = ["Recorder", "FPS"]
