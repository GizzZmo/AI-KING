# Quick Start

Use this guide to exercise AI KING locally in a few minutes. It covers the smoke tests, the deterministic orchestrator, and the cyberpunk Command Deck UI.

## Prerequisites
- Python 3.10+ (no external dependencies required)
- A C++17 compiler such as `g++` (for the settings server)
- A modern web browser

## 1) Clone and enter the repo
```bash
git clone https://github.com/GizzZmo/AI-KING.git
cd AI-KING
```

## 2) Run the smoke tests
Verify the Python orchestrator scaffold is healthy.
```bash
python -m unittest
```
You should see four tests passing in a few milliseconds.

## 3) Orchestrator in 60 seconds
Run the deterministic, checkpointed orchestrator and inspect its history.
```bash
python - <<'PY'
from pathlib import Path
from ai_king.checkpoint import CheckpointStore
from ai_king.orchestrator import GovernanceConfig, run_plan

store = CheckpointStore(Path("checkpoints"))
governance = GovernanceConfig(
    approvals_required={"ship"},
    interrupt_before=["deploy"],
)

state = run_plan(
    "Demo objective",
    ["draft plan", "review", "ship", "deploy"],
    store,
    thread_id="demo-thread",
    governance=governance,
)

print("Status:", state["status"])
print("History:", state["history"])
print("Checkpoint:", state["checkpoint_id"])
print("Approvals needed:", state["approvals_required"])
PY
```
Checkpoint snapshots are written to `checkpoints/<thread_id>/*.json` so you can replay or audit runs.

## 4) Command Deck UI & Settings API
- **Open the UI directly:** load `web/index.html` in your browser.
- **Serve the UI + APIs:** build and run the C++ settings server (defaults to port `8088`):
  ```bash
  g++ -std=c++17 -O2 -o settings_server server/settings_server.cpp
  ./settings_server
  ```
  Endpoints:
  - `GET/POST /api/prompts` (persists to `data/prompts.json`, creating the file if needed)
  - `GET/POST /api/settings` (persists to `data/settings.json`, creating the file if needed)
  - `GET /settings` to view the backend settings page
  - `GET /health` for a quick readiness check

Stop the server with `Ctrl+C`. Set the `SETTINGS_PORT` environment variable if you need a different port.

## 5) Next steps
- Dive into the [Architecture](ARCHITECTURE.md) and [Technical Blueprint](Technical%20Blueprint.md) for design details.
- Track work in the [Roadmap](ROADMAP.md).
- Read the [Orchestrator guide](wiki/Orchestrator.md) for governance hooks and extension points.
- Trademark and filing material lives in [TRADEMARK.md](TRADEMARK.md), [TRADEMARK_STRATEGY.md](TRADEMARK_STRATEGY.md), [FILING_GUIDE.md](FILING_GUIDE.md), and [NICE_CLASSIFICATIONS.md](NICE_CLASSIFICATIONS.md).
