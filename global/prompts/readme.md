# 💬 Global System Prompts

This folder contains task-specific system prompt templates designed to enforce consistency during code reviews, refactoring, and test creation.

---

## 📄 Included Prompt Templates

* **`code-review.md`**: Standardized pull request review checklist focusing on security, performance, and maintainability.
* **`generate-unit-tests.md`**: Structured prompt forcing AI assistants to write isolated unit tests following the AAA pattern.
* **`refactor-clean-code.md`**: Clean code refactoring instructions that preserve public function signatures while reducing complexity.
* **`spec-driven-development.md`**: Specify → Plan → Tasks → Implement workflow, keeping the spec as the source of truth throughout implementation.
* **`caveman-mode.md`**: Optional terse, low-token communication style (lite/default/ultra) for interim narration during long sessions. Copilot/VS Code equivalent of `global/skills/caveman/` (which self-triggers on Claude Code and covers more intensity levels — prefer it there).

---

## 🚀 Deployment Behavior

When synchronized via `tooling/sync_configs.py`, markdown files in this directory are copied directly to **`.vscode/prompts/`** for native selection inside VS Code and Copilot Chat interfaces. `readme.md` itself is skipped during deployment.

---

## 🕹️ How to Use Each Prompt

### Code Review / Generate Unit Tests / Refactor Clean Code
Select the prompt file directly from your IDE's prompt picker (`.vscode/prompts/` in VS Code / Copilot Chat), or paste its contents in as a one-off system prompt. Each is self-contained — no setup required, no other prompt depends on them.

### Spec-Driven Development (`spec-driven-development.md`)
Use this **first**, before any implementation work, on any feature that's non-trivial:

1. Invoke it with the feature request. It walks the Specify → Plan → Tasks phases, producing `specs/<NNN>-<slug>.md` and an `IMPLEMENTATION_PLAN.md` checklist.
2. Only move to the Implement phase once the spec and plan are reviewed/approved — don't let an agent implement against an unapproved spec.
3. The `specs/` and `IMPLEMENTATION_PLAN.md` files it produces are exactly what `global/agents/ralph-wiggum.yml` expects to consume — pair the two: run Spec-Driven Development to plan, then hand the resulting `IMPLEMENTATION_PLAN.md` to a Ralph loop (or a Swarm Orchestrator, for independent tasks) to implement.

### Caveman Mode (`caveman-mode.md`)
This is a style toggle, not a task prompt — layer it on top of whatever else the assistant is doing, don't use it standalone:

1. Append its contents to an existing system prompt, or tell the assistant directly (e.g. "switch to caveman mode, default level") at the start of a long session.
2. Pick a level explicitly: `lite` (safest, smallest savings), `default`, or `ultra` (biggest savings, only for rapid iterative loops you're actively watching).
3. It only affects the assistant's own interim narration and status updates — never apply it to PR descriptions, commit messages, documentation, or any other user-facing deliverable, and never let it skip a safety check or confirmation to save tokens.
