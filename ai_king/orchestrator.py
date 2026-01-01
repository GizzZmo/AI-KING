"""
Deterministic orchestrator skeleton.

This module encodes the first executable slice of the architecture
described in ARCHITECTURE.md and ROADMAP.md:
- Deterministic state machine driven by an explicit plan.
- Typed state shared across nodes.
- Checkpointing for pause/resume and history inspection.
- Human-in-the-loop breakpoints before sensitive actions.

The implementation is intentionally lightweight and dependency-free so
it can run immediately in local environments. The interfaces mirror the
planned LangGraph integration points, making it straightforward to
upgrade to a full StateGraph later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence

from .checkpoint import CheckpointStore
from .state import ExecutionStatus, GraphState


@dataclass
class GovernanceConfig:
    """
    Governance hooks for human-in-the-loop control. Sequences are used
    for caller ergonomics; the orchestrator converts them to sets for
    deterministic checks.
    """

    approvals_required: Sequence[str] = field(default_factory=list)
    interrupt_before: Sequence[str] = field(default_factory=list)


class SovereignOrchestrator:
    """Runs a deterministic, checkpointed task plan."""

    def __init__(
        self,
        store: CheckpointStore,
        governance: Optional[GovernanceConfig] = None,
        actor_name: str = "supervisor",
    ):
        self.store = store
        self.governance = governance or GovernanceConfig()
        self._approvals_required = set(self.governance.approvals_required)
        self._interrupt_before = set(self.governance.interrupt_before)
        self.actor_name = actor_name

    def bootstrap(
        self, objective: str, plan: Sequence[str], thread_id: str
    ) -> GraphState:
        state: GraphState = {
            "objective": objective,
            "plan": list(plan),
            "history": [],
            "status": "pending",
            "last_actor": self.actor_name,
            "checkpoint_id": None,
            "approvals_required": sorted(self._approvals_required),
            "approvals_granted": [],
            "errors": [],
            "context": {},
        }
        checkpoint_id = self.store.save(thread_id, state)
        state["checkpoint_id"] = checkpoint_id
        return state

    def resume(self, thread_id: str) -> Optional[GraphState]:
        return self.store.load(thread_id)

    def run_until_pause(
        self, state: GraphState, thread_id: str
    ) -> GraphState:
        """
        Execute the plan until a breakpoint, completion, or failure.
        """
        while True:
            if state["status"] in {"completed", "failed", "needs_approval"}:
                return state
            if not state["plan"]:
                state["status"] = "completed"
                return self._checkpoint(state, thread_id)

            next_task = state["plan"][0]
            if next_task in self._interrupt_before:
                state["status"] = "needs_approval"
                return self._checkpoint(state, thread_id)

            if (
                next_task in self._approvals_required
                and next_task not in state["approvals_granted"]
            ):
                state["status"] = "needs_approval"
                return self._checkpoint(state, thread_id)

            state = self._execute_task(state, next_task)
            state = self._checkpoint(state, thread_id)

    def approve_and_resume(
        self, state: GraphState, thread_id: str, task: Optional[str] = None
    ) -> GraphState:
        """
        Mark a task as approved and continue execution.

        If `task` is omitted, the next pending task is approved.
        """
        if state["status"] != "needs_approval":
            return state

        target = task or (state["plan"][0] if state["plan"] else None)
        if target is None:
            state["status"] = "failed"
            state["errors"].append("No task available to approve.")
            return self._checkpoint(state, thread_id)

        if target not in state["approvals_granted"]:
            state["approvals_granted"].append(target)

        state["status"] = "in_progress"
        return self.run_until_pause(state, thread_id)

    def _execute_task(self, state: GraphState, task: str) -> GraphState:
        """Deterministic placeholder for future agent/tool execution."""
        state["last_actor"] = self.actor_name
        state["plan"] = state["plan"][1:]
        state["history"].append(task)
        state["status"] = "in_progress" if state["plan"] else "completed"
        return state

    def _checkpoint(self, state: GraphState, thread_id: str) -> GraphState:
        checkpoint_id = self.store.save(thread_id, state)
        state["checkpoint_id"] = checkpoint_id
        return state


def run_plan(
    objective: str,
    plan: Iterable[str],
    store: CheckpointStore,
    thread_id: str = "default",
    governance: Optional[GovernanceConfig] = None,
) -> GraphState:
    """
    Convenience helper for quick-start scenarios.

    This function mirrors a simple `/invoke` API shape that can later be
    wrapped in FastAPI without changing call sites.
    """
    orchestrator = SovereignOrchestrator(store, governance=governance)
    state = orchestrator.bootstrap(objective, list(plan), thread_id=thread_id)
    return orchestrator.run_until_pause(state, thread_id=thread_id)
