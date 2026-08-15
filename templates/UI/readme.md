# 🎨 UI / Frontend Domain Overlay

Selected via `python tooling/sync_configs.py --templates UI` (or picked from the interactive menu). Overlays on top of `global/` — it doesn't replace anything, it adds frontend-specific rules on top of the baseline security/coding/testing guardrails.

---

## 📄 Included

* **`instructions/a11y.md`**: WCAG 2.2 AA accessibility standards — 38+ anti-patterns with severity, detection method, WCAG reference, and fix, plus framework-specific patterns for React/Next.js, Angular, and Vue. Adapted from [awesome-copilot.github.com/instruction/a11y](https://awesome-copilot.github.com/instruction/a11y/).

This is deliberately kept out of `global/instructions/` — it's long (~700 lines) and only relevant to projects with a UI, so a backend service or CLI tool selecting `Global only` never has it concatenated into its `copilot-instructions.md`/`CLAUDE.md`. This is the pattern for any domain-specific instruction set: put it under the matching `templates/<Domain>/instructions/`, not `global/instructions/`.

---

## ➕ Adding More

Same structure as `global/`: `templates/UI/instructions/`, `templates/UI/prompts/`, `templates/UI/agents/`, `templates/UI/skills/`. Only `instructions/` is populated today — add a `prompts/`, `agents/`, or `skills/` subfolder here the same way if a frontend-specific prompt, agent, or skill is needed later.
