"""AI agent that builds evidence-led medicomarketing strategies for HCP audiences."""

from .engine import StrategyEngine
from .phases import PHASES

__all__ = ["StrategyEngine", "PHASES"]
__version__ = "0.1.0"
