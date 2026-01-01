# Sovereign Orchestrator

The orchestrator is a deterministic, checkpointed state machine that mirrors the planned LangGraph integration points while remaining dependency-free for local runs.

## Governance Hooks
- **Approvals:** gate sensitive steps via `GovernanceConfig(approvals_required=[...])`.
- **Breakpoints:** pause before risky nodes with `interrupt_before`.
- **Human-in-the-loop:** when paused, call `approve_and_resume` to continue.

```python
from pathlib import Path
from ai_king.checkpoint import CheckpointStore
from ai_king.orchestrator import SovereignOrchestrator, GovernanceConfig

store = CheckpointStore(Path("checkpoints"))
gov = GovernanceConfig(approvals_required=["deploy"], interrupt_before=["handoff"])

orchestrator = SovereignOrchestrator(store, governance=gov)
state = orchestrator.bootstrap("Ship feature", ["draft", "review", "deploy"], "alpha")
state = orchestrator.run_until_pause(state, "alpha")   # pauses before deploy
state = orchestrator.approve_and_resume(state, "alpha")
```

## Checkpoints & History
- Snapshots live under `checkpoints/<thread_id>/*.json`.
- Use `CheckpointStore.history(thread_id)` to list past runs or recover the latest with `load`.

## Extension Points
- Replace `_execute_task` to call real agents/tools once integrated.
- Upgrade the store to a database-backed implementation while keeping the same interface.
- Wrap `run_plan` in FastAPI or LangGraph without changing call sites.
