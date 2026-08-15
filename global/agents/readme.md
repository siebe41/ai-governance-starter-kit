# 🤖 Multi-Agent Definitions

This folder contains YAML definitions establishing specialized agent roles for multi-agent workflows: a Coordinator-Worker pattern for sequential decomposition, and a Foreman-led swarm pattern (including a parallel "Ralph Swarm") for independent, parallel execution.

---

## 📄 Agent Roles

### Coordinator-Worker pattern
* **`coordinator.yml`**: High-level planner responsible for breaking complex feature requests into smaller sub-tasks.
* **`validator.yml`**: Quality assurance agent auditing proposed code changes against security standards before execution.
* **`researcher.yml`**: Read-only context gathering agent focused on exploring codebases and summarizing requirements.

### Swarm pattern (Foreman + specialists)
* **`foreman.yml`**: Leader of the swarm. Decomposes work into independent units, assigns them to the specialists below (or to Ralph Swarm Runners), and owns integration/merging.
* **`swarm-scout.yml`**: Read-only research sub-agent — investigates a unit of work before it's built.
* **`swarm-builder.yml`**: Implementation sub-agent — builds one self-contained unit of work in its own branch/worktree.
* **`swarm-auditor.yml`**: Review/test sub-agent — validates a Builder's completed work before the Foreman merges it.

### Ralph loop pattern
* **`ralph-wiggum.yml`**: Autonomous, loop-driven builder agent based on the [Ralph Wiggum technique](https://github.com/fstandhartinger/ralph-wiggum) — reads specs, implements one task per iteration, verifies, commits, and signals completion. Runs solo/sequentially.
* **`ralph-swarm-runner.yml`**: Parallel-safe variant of Ralph. Multiple runners execute the same loop at once, each claiming tasks off a shared `IMPLEMENTATION_PLAN.md` to avoid collisions, coordinated by the Foreman.

---

## 🚀 Deployment Behavior

When synchronized via `tooling/sync_configs.py`, these YAML files are packaged into **`.copilot/agents/`** for custom agent execution. `readme.md` itself is skipped during deployment — only real agent definitions land in the target repo.

---

## 🕹️ How to Use Each Pattern

### Coordinator / Validator / Researcher — single-shot custom agents
Standard request/response agents. After sync, invoke them by name from your tool's agent picker (e.g. `@Coordinator` in Copilot Chat), or lift the `system_prompt:` block straight into a Claude Code subagent definition or any other tool's custom system prompt field. One invocation produces one response — no external driver needed.

### Foreman + Swarm Scout / Builder / Auditor — parallel dispatch
1. Invoke `Foreman` once with the feature request. It returns a set of independent, non-file-overlapping unit-of-work briefs, each tagged with the specialist it needs (Scout, Builder, or Auditor).
2. Dispatch each brief to its matching specialist on its own branch/worktree — one subagent invocation per brief, run concurrently:
   - **Scout** investigates first if a brief is flagged as needing research; its report gets attached to the matching Builder's brief.
   - **Builder** implements against the brief (and any attached Scout report).
   - **Auditor** reviews a Builder's finished branch and returns `approve` or `revise` with specific notes.
3. Feed any `revise` verdicts back to the same Builder (or a fresh one) with the Auditor's notes attached.
4. Once every unit is `approve`d, invoke the Foreman again to merge all branches, resolve conflicts, and re-run the full test suite.
5. If a specialist stalls or fails, re-dispatch only that unit — don't restart the others.

Use this when work genuinely partitions with no file overlap. For tightly coupled changes where files depend on each other, use the Coordinator/Validator pattern instead — parallelizing coupled work just produces merge conflicts.

### Ralph (`ralph-wiggum.yml`) — solo loop agent
Not meant to be invoked once — it expects to be re-run repeatedly by an outer loop until the work is done:

1. Produce `specs/<NNN>-<slug>.md` files and an `IMPLEMENTATION_PLAN.md` checklist first — the **Spec-Driven Development** prompt (`global/prompts/spec-driven-development.md`) is designed to generate exactly these.
2. Optionally add `.specify/memory/constitution.md` for cross-cutting behavioral rules that should survive every iteration.
3. Wrap the `system_prompt:` in a loop script: invoke your CLI agent (Claude Code, Copilot CLI, Codex, Gemini) with it, watch the output for the literal string `<promise>DONE</promise>`, then either advance to the next unchecked task in `IMPLEMENTATION_PLAN.md` or retry the same one. The upstream [Ralph Wiggum repo](https://github.com/fstandhartinger/ralph-wiggum)'s `scripts/` folder has reference loop implementations per CLI backend — this kit ships the agent's behavioral contract, not the shell loop itself, since loop mechanics are environment-specific.
4. Stop the loop once every task in `IMPLEMENTATION_PLAN.md` is checked off.

### Ralph Swarm (`foreman.yml` + `ralph-swarm-runner.yml`) — parallel loops
For a large, well-specified `IMPLEMENTATION_PLAN.md` where tasks are independent enough to build concurrently:

1. Invoke `Foreman` to partition the plan into non-overlapping task groups, one per runner.
2. Launch one `Ralph Swarm Runner` per group, each with a distinct `runner_id`, each in its own worktree/branch, each wrapped in the same kind of loop driver as solo Ralph.
3. Runners self-coordinate collision-avoidance by claiming a task in `IMPLEMENTATION_PLAN.md` (`(claimed by: <runner_id>)`) and committing that claim before implementing it — a runner skips any task already claimed by another active runner.
4. The Foreman periodically reconciles: reassigns tasks whose claim has gone stale (no recent commit activity), and merges each runner's branch as it signals `<promise>DONE</promise>`.
5. Stop when every task across every runner's group is checked off and merged.

Prefer plain Ralph when a plan is small enough to run sequentially without the coordination overhead; reach for Ralph Swarm when the plan is large and the tasks are genuinely independent.

---

## 📐 Why YAML, Not Markdown?

Every file in this folder is YAML, matching `coordinator.yml`/`validator.yml`. This isn't inconsistent with `global/prompts/` being Markdown; it's required by the deployment target each folder feeds:

* `global/agents/` → `.copilot/agents/*.yml` (GitHub Copilot's custom-agent config format is YAML).
* `global/prompts/` → `.vscode/prompts/*.md` (VS Code / Copilot Chat prompt files are Markdown).

`build_copilot_target()` in `tooling/sync_configs.py` glob-copies this folder's contents as-is, so every file here needs to already be valid Copilot agent YAML. If you need an agent's behavior as a Markdown system prompt for a tool that expects one (e.g. a Claude Code subagent `.md` file with frontmatter), copy the `system_prompt:` block out of the YAML — it's plain text, written to be lifted directly with no reformatting.
