# AI KING Implementation Roadmap

This roadmap operationalizes the phases defined in **Technical Blueprint.md**, translating the architectural vision into concrete, verifiable delivery steps.

## Phase 1 – Sovereign Foundation (Core Orchestration)
- **Objectives:** Establish deterministic control, typed global state, and durable execution.
- **Deliverables:**
  - LangGraph **StateGraph** deployed behind FastAPI with strictly typed state (Pydantic model or TypedDict as baseline).
  - Postgres-backed **checkpointing** (e.g., AsyncPostgresSaver) with thread-scoped resumability and history inspection.
  - Initial **Supervisor** node powered by a high-reasoning model (e.g., GPT-4o/Claude 3.5).
  - Governance hooks for **human-in-the-loop breakpoints** before sensitive actions.
- **Exit Criteria:** End-to-end task run can be paused/resumed from checkpoints; state inspection and manual edits are supported.

## Phase 2 – Council of Experts (Specialization & Tooling)
- **Objectives:** Add delegation, specialist agents, and safe tool use.
- **Deliverables:**
  - Supervisor routing to **Researcher, Coder, and Critic** agents using `create_react_agent`.
  - **MCP servers** for filesystem/utilities plus **remote sandboxed code execution** (E2B/CodeGate) for interpreter tasks.
  - Policy-enforced tool permissions and logging for agent actions.
  - Trace collection for tool calls to seed future fine-tuning datasets.
- **Exit Criteria:** Multi-agent task completes with tool calls audited; failing outputs are routed to the Critic before completion.

## Phase 3 – Royal Archives (Deep Memory)
- **Objectives:** Provide long-term semantic memory and knowledge grounding.
- **Deliverables:**
  - **GraphRAG pipeline** with Neo4j/FalkorDB: entity/relation extraction, deduplication, and Cypher-based retrieval.
  - Hybrid memory that combines checkpointed short-term state with graph-backed long-term context injection.
  - **Memory Manager** background job for consolidation (merge duplicates, prune stale edges).
- **Exit Criteria:** Queries return graph-grounded contexts; episodic summaries are stored and retrievable for plan warm-starts.

## Phase 4 – Coronation (GGI & Autonomy)
- **Objectives:** Enhance decision quality and self-improvement.
- **Deliverables:**
  - **Mixture-of-Agents (MoA)** proposer/aggregator pattern for Supervisor decisions.
  - **Recursive Self-Improvement (RSI)** loop (Generator → Critic → retry) with a Teacher agent that updates system prompts from trace analysis.
  - **Observability** via LangSmith (or equivalent) on all nodes for latency, cost, and failure forensics.
- **Exit Criteria:** MoA improves task success vs. single-model baseline; prompt updates are versioned and rolled out from Teacher findings.

## Tracking & Dependencies
- **Foundational dependencies:** Kubernetes/Fargate deployment, Postgres with backups, secret management for model/tool credentials.
- **Security & Governance:** Explicit approval gates for external tools, remote sandboxing for code execution, RBAC for MCP servers.
- **Success Metrics (examples):** checkpoint resume rate, tool-call failure rate, MoA win-rate over baseline, mean time to repair via Teacher updates.

## References
- See **Technical Blueprint.md** for the underlying architectural rationale and detailed subsystem specifications.
