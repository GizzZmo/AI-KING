"""
Lightweight checkpoint store.

The technical blueprint emphasizes resumability and history inspection.
This file provides a filesystem-backed implementation that is simple to
swap for Postgres later. It keeps the interface narrow so production
stores can reuse the same contract.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable, Optional, Tuple

from .state import GraphState


class CheckpointStore:
    """Persist and retrieve graph state snapshots."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path_for(self, thread_id: str, checkpoint_id: str) -> Path:
        return self.base_path / thread_id / f"{checkpoint_id}.json"

    def save(self, thread_id: str, state: GraphState) -> str:
        checkpoint_id = state.get("checkpoint_id") or self._timestamp()
        state = {**state, "checkpoint_id": checkpoint_id}
        path = self._path_for(thread_id, checkpoint_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return checkpoint_id

    def load(
        self, thread_id: str, checkpoint_id: Optional[str] = None
    ) -> Optional[GraphState]:
        target_id = checkpoint_id or self._latest_id(thread_id)
        if target_id is None:
            return None
        path = self._path_for(thread_id, target_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)  # type: ignore[return-value]

    def history(self, thread_id: str) -> Iterable[Tuple[str, Path]]:
        thread_dir = self.base_path / thread_id
        if not thread_dir.exists():
            return []
        snapshots = sorted(thread_dir.glob("*.json"))
        return [(p.stem, p) for p in snapshots]

    def _latest_id(self, thread_id: str) -> Optional[str]:
        snapshots = list(self.history(thread_id))
        return snapshots[-1][0] if snapshots else None

    @staticmethod
    def _timestamp() -> str:
        return str(int(time.time() * 1000))
