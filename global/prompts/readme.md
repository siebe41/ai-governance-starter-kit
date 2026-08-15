# 💬 Global System Prompts

This folder contains task-specific system prompt templates designed to enforce consistency during code reviews, refactoring, and test creation.

---

## 📄 Included Prompt Templates

* **`code-review.md`**: Standardized pull request review checklist focusing on security, performance, and maintainability.
* **`generate-unit-tests.md`**: Structured prompt forcing AI assistants to write isolated unit tests following the AAA pattern.
* **`refactor-clean-code.md`**: Clean code refactoring instructions that preserve public function signatures while reducing complexity.
* **`spec-driven-development.md`**: Specify → Plan → Tasks → Implement workflow, keeping the spec as the source of truth throughout implementation.
* **`caveman-mode.md`**: Optional terse, low-token communication style (lite/default/ultra) for interim narration during long sessions.

---

## 🚀 Deployment Behavior

When synchronized via `tooling/sync_configs.py`, markdown files in this directory are copied directly to **`.vscode/prompts/`** for native selection inside VS Code and Copilot Chat interfaces.