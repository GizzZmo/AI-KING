"""
Typed state definitions for the AI KING sovereign orchestrator.

The roadmap calls for strictly typed state (Pydantic or TypedDict). To
avoid pulling runtime dependencies at this early stage, we use
``TypedDict`` with narrow literals to model the state that flows through
the graph. This keeps the contract explicit while remaining lightweight
enough to bootstrap quickly.
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional, TypedDict


ExecutionStatus = Literal[
    "pending",
    "in_progress",
    "needs_approval",
    "waiting",
    "completed",
    "failed",
]


class GraphState(TypedDict):
    """
    Minimal deterministic state container.

    Keys:
    - objective: high-level mission text
    - plan: ordered list of tasks still to execute
    - history: log of executed tasks
    - status: lifecycle marker for the orchestrator
    - last_actor: the actor that last mutated state (supervisor/agent)
    - checkpoint_id: identifier of the last persisted checkpoint
    - approvals_required: tasks that require human approval before run
    - approvals_granted: tasks that have been approved
    - errors: captured error messages
    - context: free-form dictionary for downstream agents
    """

    objective: str
    plan: List[str]
    history: List[str]
    status: ExecutionStatus
    last_actor: Optional[str]
    checkpoint_id: Optional[str]
    approvals_required: List[str]
    approvals_granted: List[str]
    errors: List[str]
    context: Dict[str, str]
