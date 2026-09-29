# 🧠 Claude Skills

This folder contains [Claude Code Skills](https://github.com/obra/superpowers) — self-contained, procedural `SKILL.md` files that Claude Code loads natively and invokes by name when their `description` matches the task at hand. Unlike `global/prompts/` (a file you select manually) or `global/agents/` (a role you invoke), a skill is meant to trigger itself.

---

## 📄 Included Skills

### Governance protocol
* **`learnings-log/`**: Self-triggering enforcement of the mistakes/gotchas protocol — reads `LEARNINGS.md` at the start of every task, and appends to it immediately after a correction or a non-obvious gotcha. See `global/instructions/03-learnings-log.md` for the full protocol this enforces.

### Team & codebase orchestration
* **`ai-team-orchestration/`**: Bootstraps the `ai-team-producer`/`ai-team-dev`/`ai-team-qa` agents into a working Plan → Implement → Test → optional review/QA → Merge loop, with reference templates for a project brief, sprint plan, and brainstorm format. See `global/agents/readme.md`'s "AI Team pattern" for the agent roles this coordinates.
* **`acquire-codebase-knowledge/`**: Maps an existing codebase into seven evidence-based docs (`STACK.md`, `STRUCTURE.md`, `ARCHITECTURE.md`, `CONVENTIONS.md`, `INTEGRATIONS.md`, `TESTING.md`, `CONCERNS.md`) under `docs/codebase/`. Ships a Python scan script (`scripts/scan.py`, stdlib-only, read-only — file/manifest detection plus `git log`/churn) and templates for each doc. Every claim must trace to a file, config, or terminal output; unknowns get `[TODO]`, team-intent questions get `[ASK USER]`.

### Caveman family — terse, token-efficient communication
* **`caveman/`**: Ultra-compressed response mode (lite/full/ultra + wenyan variants). Self-triggers on "caveman mode", "less tokens", "be brief", or `/caveman`. This is the Claude-native counterpart to `global/prompts/caveman-mode.md` — prefer this skill on Claude Code, since it self-triggers and covers more intensity levels; the prompt exists for Copilot/VS Code, which have no native Skills system to self-trigger from.
* **`caveman-commit/`**: Terse Conventional Commits messages — subject ≤50 chars, body only when the "why" isn't obvious.
* **`caveman-review/`**: One-line-per-finding PR review comments (`L42: bug: user null. Add guard.`).
* **`caveman-help/`**: One-shot quick-reference card for every caveman mode/skill/trigger.
* **`compress/`** and **`caveman-compress/`**: Compress a natural-language memory file (e.g. `CLAUDE.md`) into caveman-speak in place, backing up the original as `<file>.original.md`. These two are near-duplicates of each other (same rules, different script-path resolution) — flagged for cleanup in `CHANGELOG.md`/`LEARNINGS.md` rather than merged unilaterally, since which one is canonical is a call for this repo's maintainer.

### Engineering discipline skills — adapted from `obra/superpowers`
* **`test-driven-development/`**: Enforces the red-green-refactor discipline behind `global/instructions/02-testing-standards.md` — no production code without a failing test first.
* **`using-git-worktrees/`**: Sets up an isolated workspace (native tool first, git worktree fallback) before feature work or a multi-step implementation plan — the isolation primitive the Swarm and Ralph Swarm agents assume exists.
* **`finishing-a-development-branch/`**: Verifies tests, then presents merge/PR/keep-as-is options and waits for a decision — never guesses whether to merge or discard.

The three engineering-discipline skills are adapted from [obra/superpowers](https://github.com/obra/superpowers) (MIT License, © Jesse Vincent) — condensed and re-worded to match this kit's tone, with source and license credited at the bottom of each `SKILL.md`.

---

## 🚫 Deliberately Not Included: `ai-ready`

[awesome-copilot's `ai-ready` skill](https://awesome-copilot.github.com/skill/ai-ready/) is a thin wrapper whose entire job is telling the user to run `/skills add johnpapa/ai-ready` — installing a ~600-line, frequently-changing skill from a third-party repo at runtime. This kit's own `00-security-governance.md` says "No Untrusted Dependencies: Do not introduce third-party packages or libraries without verifying their license and security posturing" — vendoring a wrapper whose function is "auto-install an unreviewed external skill" would violate that rule from inside the kit that states it. It's also redundant: `ai-ready`'s stated purpose (generate `AGENTS.md`/`copilot-instructions.md`/CI config customized to your stack) is what `tooling/aigov.py` already does, natively and reviewed, for this kit. If you specifically want the upstream `johnpapa/ai-ready` skill, install it directly per its own instructions — just know it sits outside this kit's review process.

---

## 🚀 Deployment Behavior

Each subfolder here is one skill: a `SKILL.md` (frontmatter `name` + `description`, then the procedure), optionally with a `scripts/` folder or other reference files it uses. aigov copies every skill folder wholesale to `.github/skills/<name>/` for GitHub Copilot or `.claude/skills/<name>/` for Claude Code (once, to `.claude/skills/`, when a repo uses both, since Copilot reads that folder too). See [`TARGETS.md`](/TARGETS.md). `readme.md` is not a skill folder, so it's never deployed.

GitHub Copilot and Claude Code discover skills in their skills folders automatically and decide on their own when a skill's `description` matches the current task. You can also run one by name (`/skill-name`).

---

## ➕ Adding Your Own Skill

1. Create `global/skills/<your-skill-name>/SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: your-skill-name
   description: One sentence stating exactly when this should trigger — specific enough that it won't fire on unrelated tasks.
   ---
   ```
2. Write the procedure as plain, imperative Markdown — steps, decision tables, and a "common rationalizations" table if the skill exists to stop a specific corner-cutting failure mode (see the three engineering-discipline skills for the pattern).
3. Add it to the **Included Skills** list above.
4. If you don't want it maintained centrally, you don't need to touch this folder at all — see the top-level `README.md`'s "Include/Exclude & Bring Your Own" section for adding project-specific skills without editing the vendored kit.
