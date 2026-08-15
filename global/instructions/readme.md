# 📜 Global AI Instructions & Rules

The markdown files in this folder define the non-negotiable corporate guardrails and coding standards for AI models working within your codebase.

---

## 📄 File Naming & Precedence Conventions

To ensure instructions are merged in a predictable sequence, prefix files with numeric ordering:

* **`00-security-governance.md`**: Secret handling, PII sanitization, and enterprise compliance rules (highest priority).
* **`01-coding-standards.md`**: Architecture, error handling, logging, and design principles.
* **`02-testing-standards.md`**: Unit and integration test expectations, isolation rules, and coverage thresholds.
* **`03-learnings-log.md`**: Protocol requiring AI assistants to read and append to a per-repo `LEARNINGS.md` file so mistakes, corrections, and gotchas are never repeated.
* **`04-context-engineering.md`**: Project structure and coding-pattern guidance (paths, types, naming, colocated code) that helps any AI assistant — not just one vendor's — give better suggestions and make better changes.

---

## 🚀 Deployment Behavior

During deployment (`python tooling/sync_configs.py`), all `.md` files in this directory—alongside any selected domain template instructions—are concatenated into a single **`.github/copilot-instructions.md`** file for GitHub Copilot Workspace.

Separately, the `03-learnings-log.md` protocol is backed by a seeded **`LEARNINGS.md`** file at the target repository root (see `global/LEARNINGS.template.md`). Unlike the concatenated instructions, this file is never overwritten once it exists, since it accumulates project-specific learnings over time.