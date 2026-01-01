# Getting Started

## Quick Run
- **Smoke tests:** `python -m unittest`
- **Command Deck UI:** open `web/index.html` directly or build the settings server:  
  `g++ -std=c++17 -O2 -o settings_server server/settings_server.cpp && ./settings_server`
- **API endpoints:** `GET/POST /api/prompts`, `GET/POST /api/settings`, and `GET /settings` (served by the settings server on port `8088` by default).

## Orchestrator Smoke Example
```python
from pathlib import Path
from ai_king.checkpoint import CheckpointStore
from ai_king.orchestrator import run_plan, GovernanceConfig

store = CheckpointStore(Path("checkpoints"))
governance = GovernanceConfig(
    approvals_required=["ship"],
    interrupt_before=["deploy"],
)

state = run_plan(
    "Demo objective",
    ["draft plan", "review", "ship", "deploy"],
    store,
    thread_id="demo-thread",
    governance=governance,
)

print(state["status"])
print(state["history"])
```

Checkpoint snapshots will be written to `checkpoints/<thread_id>/` so you can inspect and replay execution.

## Repo Map
- `ai_king/` — deterministic orchestrator, governance hooks, and checkpoint store.
- `web/` — HTML5 Command Deck interface (cyberpunk theme).
- `server/` — C++ settings server that feeds the UI.
- `data/` — prompt and settings payloads for the UI/server APIs.
