import json
import sys
import tempfile
from pathlib import Path
from typing import List
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_king.checkpoint import CheckpointStore
from ai_king.orchestrator import GovernanceConfig, SovereignOrchestrator, run_plan


class OrchestratorTests(unittest.TestCase):
    def _store(self) -> CheckpointStore:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return CheckpointStore(Path(tmp.name))

    def test_runs_plan_and_persists_history(self) -> None:
        store = self._store()
        state = run_plan(
            "demo",
            ["research", "draft"],
            store,
            thread_id="t1",
            governance=GovernanceConfig(),
        )
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["history"], ["research", "draft"])
        restored = store.load("t1")
        self.assertIsNotNone(restored)
        assert restored  # type narrowing
        self.assertEqual(restored["history"], ["research", "draft"])

    def test_breakpoint_requires_human_approval(self) -> None:
        store = self._store()
        governance = GovernanceConfig(approvals_required={"deploy"})
        orchestrator = SovereignOrchestrator(store, governance=governance)
        state = orchestrator.bootstrap(
            "demo", ["lint", "deploy", "notify"], thread_id="t2"
        )
        paused = orchestrator.run_until_pause(state, thread_id="t2")
        self.assertEqual(paused["status"], "needs_approval")
        self.assertEqual(paused["plan"][0], "deploy")

        resumed = orchestrator.approve_and_resume(paused, "t2")
        self.assertEqual(resumed["status"], "completed")
        self.assertEqual(resumed["history"], ["lint", "deploy", "notify"])

    def test_checkpoint_history_listing(self) -> None:
        store = self._store()
        governance = GovernanceConfig(interrupt_before={"review"})
        orchestrator = SovereignOrchestrator(store, governance=governance)
        state = orchestrator.bootstrap("demo", ["review"], thread_id="t3")
        paused = orchestrator.run_until_pause(state, "t3")
        history: List = list(store.history("t3"))
        self.assertEqual(len(history), 1)
        checkpoint_id, path = history[0]
        with path.open() as fh:
            loaded = json.load(fh)
        self.assertEqual(loaded["checkpoint_id"], checkpoint_id)
        self.assertEqual(paused["status"], "needs_approval")


if __name__ == "__main__":
    unittest.main()
