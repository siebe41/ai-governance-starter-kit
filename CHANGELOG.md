# Changelog

All notable changes to this starter kit are documented here. Versions follow [Semantic Versioning](https://semver.org/):

* **major** — breaking changes to file paths, generated output formats, or anything that changes a downstream project's existing assumptions.
* **minor** — new instructions, agents, prompts, or templates that are additive.
* **patch** — wording fixes, doc corrections, no behavioral change.

Every change to `global/`, `templates/`, or `tooling/sync_configs.py` should bump this file and `VERSION` — see `CONTRIBUTING.md`.

---

## [1.5.1]

### Fixed
- `global/mcp/mcp-servers.json`'s `graft` entry now pins an exact version (`@nanonets/graft@0.16.0` instead of the unpinned `@nanonets/graft`) — flagged by an AgentShield (`ecc-agentshield`) security scan run against a project synced from this kit: an unpinned `npx -y` package auto-installs whatever is newest at MCP-server-launch time, so a future compromised publish to that package would run automatically. The other three entries (`azure-devops`, `github`, `filesystem`) have the same unpinned-`npx` shape and were flagged too, but are illustrative placeholders an org is expected to replace with its own approved servers — not fixed here for that reason. Left `-y` in place rather than removing it (AgentShield's other suggestion): Claude Code launches MCP servers non-interactively, and `npx` without `-y` would have no TTY to prompt, likely hanging or failing the server outright — pinning the version already closes the "arbitrary future publish" gap `-y` was flagged for. Also considered and declined: adding an explicit `env: {}` block to strip inherited environment variables (AgentShield's third suggestion) — Claude Code's documented MCP config behavior treats `env` as additive to the inherited environment, not a replacement, so an empty block would likely be a no-op at best and, if that assumption is wrong for a given host, could strip `PATH` and break `npx` itself. Left as an open question rather than guessed at.

---

## [1.5.0]

### Added
- **`hooks` as a fifth canonical asset category**, alongside `instructions`/`prompts`/`agents`/`skills`. A hook is what turns a "the model should always do X" `global/instructions/` rule into something the harness enforces outside model context (a Claude Code [hook](https://docs.claude.com/en/docs/claude-code/hooks)), rather than something that depends on the model remembering a written instruction on every turn.
- `global/hooks/lint-before-finish.json` — a `Stop` hook fragment that, when the working tree has an uncommitted change, runs `npm run lint` and blocks finishing until it passes, with the lint output fed back as the reason. Silent no-op on a clean tree.
- `global/hooks/readme.md` — category docs (deployment behavior, a security note specific to this category since it's the one whose assets execute shell commands rather than only being read by a model, and how to add your own).
- `tooling/sync_configs.py`: `build_hooks_target()` deploys `global/hooks/*.json` fragments into a target repo's `.claude/settings.json`. Unlike every other category (a directory copy or a wholesale file rewrite), this is a **merge**: existing top-level keys and hooks already in the target's `settings.json` are preserved, a fragment already present from a prior sync is skipped (idempotent re-run), and a `settings.json` that fails to parse is left untouched with a warning rather than risked.
- `CATEGORIES` now includes `"hooks"`, so `.ai-governance.json`'s `exclude`/`local_dirs` support it the same way as the other four categories (exclude by the fragment's filename stem; `local_dirs` for a project's own hook fragments, layered in the same merge).

### Changed
- `README.md`: folder hierarchy, architecture diagram, CLI walkthrough transcript, and the Include/Exclude & Bring Your Own section all updated for the new category; added a "Global Hooks" section alongside "Included Skills"/"Global MCP Integration".

---

## [1.4.0]

### Added
- `graft` entry in `global/mcp/mcp-servers.json` — [trailhq/Graft](https://github.com/trailhq/Graft) (`@nanonets/graft`, MIT), an MCP server that serves a local tree-sitter-built codebase graph to any MCP-capable agent. Requires no secret, contacts no service by default, and only activates in a project once a developer runs `npx graft init` there — see `README.md`'s "Global MCP Integration" section and `global/skills/readme.md`'s `acquire-codebase-knowledge` entry for how the two compare.

### Declined
- [affaan-m/ECC](https://github.com/affaan-m/ECC) ("Everything Claude Code") was evaluated alongside Graft and deliberately not vendored. On inspection the hook/install code itself wasn't malicious (hooks require an explicit `--enable-hooks` flag; the sampled hook scripts — governance-capture, observe-runner, cost-tracker, desktop-notify — made no network calls), but: its claimed ~250k GitHub stars are implausible for a repo of this age/niche and consistent with fake-star inflation; an independent audit found its own virality has already produced a malware-dropper clone in the wild; and it is a ~9,000-file, 68-agent, 286-skill bundle from a single maintainer shipping weekly, hooking nearly every tool call. That combination of unverifiable popularity, adjacent malware risk, and unauditable surface area conflicts with this kit's own `00-security-governance.md` "No Untrusted Dependencies" rule and its "curated, single source of truth" design — same reasoning class as the `ai-ready` decline in `[1.3.0]`, at much larger scale. If a specific ECC skill/agent/rule is wanted later, cherry-pick and hand-review that one file rather than vendoring the bundle.

---

## [1.3.0]

### Added
- `global/skills/learnings-log/` — self-triggering Claude Code Skill enforcement of the mistakes/learnings protocol (reads `LEARNINGS.md` at task start, appends after a correction/gotcha), complementing `global/instructions/03-learnings-log.md` for tools without a Skills system.
- **AI Team agent pattern**: `global/agents/ai-team-producer.yml`, `ai-team-dev.yml`, `ai-team-qa.yml` plus `global/skills/ai-team-orchestration/` (with project-brief, sprint-plan, and brainstorm-format references) — a small persistent team with real merge authority and proportional process, distinct from the single-shot Coordinator-Worker pattern.
- `global/agents/plan.yml` — standalone strategic-planning agent (think first, code later); pairs with any implementation pattern.
- `global/agents/se-technical-writer.yml` — documentation/blog/tutorial/ADR/user-guide specialist with a template per content type.
- `global/skills/acquire-codebase-knowledge/` — maps an existing codebase into seven evidence-based docs under `docs/codebase/`, with a bundled read-only Python scan script and templates.
- `global/instructions/04-context-engineering.md` — universal project-structure guidance for AI-assistant legibility (applies regardless of vendor).
- `templates/UI/instructions/a11y.md` — WCAG 2.2 AA accessibility standards (38+ anti-patterns, framework-specific fixes) — the first populated domain template, and a template for `templates/readme.md`'s global-vs-domain rule of thumb.
- All of the above adapted from the `awesome-copilot.github.com` catalog (agent/instruction/skill pages named by the maintainer), credited by source URL in each file.

### Changed
- `global/agents/readme.md` restructured with a "Which Pattern Should I Use?" table now that there are 4 patterns (Coordinator-Worker, AI Team, Swarm, Ralph) plus 2 standalone specialists (Plan, Technical Writer) — several overlap in purpose and the right choice depends on how work partitions.

### Declined
- `awesome-copilot`'s `ai-ready` skill was evaluated and deliberately not vendored: its entire function is instructing the user to install a third-party skill at runtime (`/skills add johnpapa/ai-ready`), which conflicts with this kit's own "No Untrusted Dependencies" rule (`00-security-governance.md`) and duplicates what `tooling/sync_configs.py` already does natively. See `global/skills/readme.md` for the full reasoning.

---

## [1.2.0]

### Added
- **Per-project include/exclude selection.** Every sync now writes `.ai-governance.json` at the target repo root (domain templates + an `exclude` list per category); a saved selection is reused on future syncs without re-prompting, `--templates` on the CLI always overrides it, and `--reconfigure` discards it and re-selects from scratch.
- **"Bring your own" local overrides.** `.ai-governance.json`'s `local_dirs` lets a project register its own folders (e.g. `governance-local/instructions/`, `governance-local/skills/`) that get merged into the sync alongside canonical `global/` assets, so project-specific additions survive re-vendoring the kit via subtree/submodule updates without touching vendored files.
- **`global/skills/` category** and a new `.claude/skills/<name>/` deployment target (`build_skills_target()`) for Claude Code's native Skills system — skills are folders (`SKILL.md` + optional `scripts/`), copied and excluded by folder name rather than filename.
- `global/skills/test-driven-development/`, `using-git-worktrees/`, `finishing-a-development-branch/` — adapted from [obra/superpowers](https://github.com/obra/superpowers) (MIT, © Jesse Vincent), credited in each file.

### Fixed
- `global/skills/readme.md` now documents the full skill roster, including the pre-existing `caveman`/`caveman-commit`/`caveman-review`/`caveman-help`/`compress`/`caveman-compress` family (commit `1e9ccd9`) that a `global/skills/` folder scan missed during this release's planning — cross-referenced against `global/prompts/caveman-mode.md`, which now points Claude Code users at the richer, self-triggering `global/skills/caveman/` instead.

### Known Limitations
- Excluding an already-deployed asset doesn't retroactively delete the file a previous sync wrote — `sync_configs.py` only adds/updates, it doesn't prune. Documented in the main `README.md`.
- `global/skills/compress/` and `global/skills/caveman-compress/` are near-duplicates (same rules, different script-path resolution) — left as-is pending a maintainer decision on which is canonical.

---

## [1.1.0]

### Added
- `global/instructions/03-learnings-log.md` — mandatory protocol requiring AI assistants to read and append to a per-repo `LEARNINGS.md` mistakes/gotchas log before repeating a correction.
- `global/LEARNINGS.template.md`, seeded into every synced repo as `LEARNINGS.md` — never overwritten once it exists.
- `global/agents/foreman.yml`, `swarm-scout.yml`, `swarm-builder.yml`, `swarm-auditor.yml` — a Foreman-led swarm pattern (research → implement → audit, dispatched to independent units in parallel).
- `global/agents/ralph-wiggum.yml` — solo autonomous loop-driven builder agent, based on the [Ralph Wiggum technique](https://github.com/fstandhartinger/ralph-wiggum).
- `global/agents/ralph-swarm-runner.yml` — parallel-safe Ralph variant; multiple runners claim tasks off a shared `IMPLEMENTATION_PLAN.md` to avoid collisions, coordinated by the Foreman.
- `global/agents/researcher.yml` — closes a gap where the Coordinator-Worker pattern's readme documented a Researcher agent with no backing file.
- `global/prompts/spec-driven-development.md` — Specify → Plan → Tasks → Implement workflow prompt.
- `global/prompts/caveman-mode.md` — optional terse, low-token communication style for an assistant's own interim narration.
- `CLAUDE.md` deployment target — `sync_configs.py` now generates a Claude Code / Agent SDK config alongside `.github/copilot-instructions.md`, matching the README's stated tool support.
- A version-stamp header (`<!-- Generated by ai-governance-starter-kit vX.Y.Z ... -->`) is now prepended to every generated `copilot-instructions.md` / `CLAUDE.md`, so a downstream repo can tell which version of the org's rules it last synced.
- `CONTRIBUTING.md`, `VERSION`, this `CHANGELOG.md`, `QUICKSTART.md`, and a root `.gitignore` for this canonical repo.

### Fixed
- `build_vscode_target()` / `build_copilot_target()` no longer copy each folder's own `readme.md` into the deployed `.vscode/prompts/` and `.copilot/agents/` directories.

### Changed
- Removed `global/agents/swarm-orchestrator.yml` and `swarm-worker.yml`, superseded by the Foreman + Scout/Builder/Auditor set above.

---

## [1.0.0] — Initial Release

- Baseline `global/instructions/`: security governance, coding standards, testing standards.
- `global/agents/coordinator.yml`, `validator.yml`.
- `global/prompts/code-review.md`, `generate-unit-tests.md`, `refactor-clean-code.md`.
- `global/mcp/mcp-servers.json` central MCP server registry.
- `tooling/sync_configs.py` multi-target deployment engine (`.github/`, `.vscode/`, `.copilot/`).
- `docs/governance-playbook.md`, `docs/architecture-diagrams.md`.
