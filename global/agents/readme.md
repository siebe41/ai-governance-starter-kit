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

When synchronized via `tooling/sync_configs.py`, these YAML files are packaged into **`.copilot/agents/`** for custom agent execution. `readme.md` itself is skipped during deployment — only real agent definitions land in the target repo.

---

## 🕹️ How to Use Each Agent

### Coordinator / Validator / Researcher — single-shot custom agents
Standard request/response agents. After sync, invoke them by name from your tool's agent picker (e.g. `@Coordinator` in Copilot Chat), or lift the `system_prompt:` block straight into a Claude Code subagent definition or any other tool's custom system prompt field. One invocation produces one response — no external driver needed.

### Ralph (`ralph-wiggum.yml`) — loop agent
This one is **not** meant to be invoked once. It expects to be re-run repeatedly by an outer loop until the work is done:

1. Produce `specs/<NNN>-<slug>.md` files and an `IMPLEMENTATION_PLAN.md` checklist first — the **Spec-Driven Development** prompt (`global/prompts/spec-driven-development.md`) is designed to generate exactly these.
2. Optionally add `.specify/memory/constitution.md` for cross-cutting behavioral rules that should survive every iteration.
3. Wrap the `system_prompt:` in a loop script: invoke your CLI agent (Claude Code, Copilot CLI, Codex, Gemini) with it, watch the output for the literal string `<promise>DONE</promise>`, then either advance to the next unchecked task in `IMPLEMENTATION_PLAN.md` or retry the same one. The upstream [Ralph Wiggum repo](https://github.com/fstandhartinger/ralph-wiggum)'s `scripts/` folder has reference loop implementations per CLI backend — this kit ships the agent's behavioral contract, not the shell loop itself, since loop mechanics are environment-specific.
4. Stop the loop once every task in `IMPLEMENTATION_PLAN.md` is checked off.

### Swarm (`swarm-orchestrator.yml` + `swarm-worker.yml`) — parallel dispatch
1. Invoke `Swarm Orchestrator` once with the feature request. It should return a set of independent, non-file-overlapping unit-of-work briefs.
2. For each brief, start a separate `Swarm Worker` invocation on its own branch or worktree (one Claude Code subagent per brief, one CI job per brief, etc.), giving it only that brief — never the full task list.
3. Once all workers report back, invoke the Orchestrator again to merge branches, resolve any integration conflicts, and re-run the full test suite.
4. If a worker fails or stalls, re-dispatch only that unit — don't restart the others.

Use Swarm when work genuinely partitions with no file overlap. For tightly coupled changes where files depend on each other, use the Coordinator/Validator pattern instead — parallelizing coupled work will just produce merge conflicts.

---

## 📐 Why YAML, Not Markdown?

Every file in this folder is YAML — including the newer `ralph-wiggum.yml` and `swarm-*.yml` — matching `coordinator.yml` and `validator.yml`. This isn't inconsistent with `global/prompts/` being Markdown; it's required by the deployment target each folder feeds:

* `global/agents/` → `.copilot/agents/*.yml` (GitHub Copilot's custom-agent config format is YAML).
* `global/prompts/` → `.vscode/prompts/*.md` (VS Code / Copilot Chat prompt files are Markdown).

`build_copilot_target()` in `tooling/sync_configs.py` glob-copies this folder's contents as-is, so every file here needs to already be valid Copilot agent YAML. If you need Ralph's or Swarm's behavior as a Markdown system prompt for a tool that expects one (e.g. a Claude Code subagent `.md` file with frontmatter), copy the `system_prompt:` block out of the YAML — it's plain text, written to be lifted directly with no reformatting.
