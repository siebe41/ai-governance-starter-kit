# 🤖 Multi-Agent Definitions

This folder contains YAML definitions establishing specialized agent roles for multi-agent workflows (such as Coordinator-Worker patterns).

---

## 📄 Agent Roles

* **`coordinator.yml`**: High-level planner responsible for breaking complex feature requests into smaller sub-tasks.
* **`validator.yml`**: Quality assurance agent auditing proposed code changes against security standards before execution.
* **`researcher.yml`**: Read-only context gathering agent focused on exploring codebases and summarizing requirements.
* **`ralph-wiggum.yml`**: Autonomous, loop-driven builder agent based on the [Ralph Wiggum technique](https://github.com/fstandhartinger/ralph-wiggum) — reads specs, implements one task per iteration, verifies, commits, and signals completion.
* **`swarm-orchestrator.yml`**: Decomposes work into independent units and dispatches them to isolated `Swarm Worker` agents running in parallel.
* **`swarm-worker.yml`**: Executes a single, self-contained unit of work dispatched by the `Swarm Orchestrator`, scoped to its own branch/worktree.

---

## 🚀 Deployment Behavior

When synchronized via `tooling/sync_configs.py`, these YAML files are packaged into **`.copilot/agents/`** for custom agent execution.