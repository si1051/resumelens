"""Pure-Python analysis engine. No web framework imports here so it can be reused and unit tested."""

from .scorer import analyze

__all__ = ["analyze"]
