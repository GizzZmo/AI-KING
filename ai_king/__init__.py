"""
AI KING prototype package.

This package provides the first executable scaffolding outlined in the
architecture and roadmap documents. The goal is a deterministic,
checkpointed orchestration skeleton that can later be swapped for
LangGraph-based components without changing calling code.
"""

from .state import GraphState, ExecutionStatus  # noqa: F401
from .checkpoint import CheckpointStore  # noqa: F401
from .orchestrator import SovereignOrchestrator  # noqa: F401

