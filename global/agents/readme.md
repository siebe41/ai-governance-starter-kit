# 🤖 Multi-Agent Definitions

This folder contains YAML definitions establishing specialized agent roles for multi-agent workflows (such as Coordinator-Worker patterns).

---

## 📄 Agent Roles

* **`coordinator.yml`**: High-level planner responsible for breaking complex feature requests into smaller sub-tasks.
* **`validator.yml`**: Quality assurance agent auditing proposed code changes against security standards before execution.
* **`researcher.yml`**: Read-only context gathering agent focused on exploring codebases and summarizing requirements.

---

## 🚀 Deployment Behavior

When synchronized via `tooling/sync_configs.py`, these YAML files are packaged into **`.copilot/agents/`** for custom agent execution.