# Changelog

All notable changes to this starter kit are documented here. Versions follow [Semantic Versioning](https://semver.org/):

* **major** — breaking changes to file paths, generated output formats, or anything that changes a downstream project's existing assumptions.
* **minor** — new instructions, agents, prompts, or templates that are additive.
* **patch** — wording fixes, doc corrections, no behavioral change.

Every change to `global/`, `templates/`, or `tooling/aigov.py` should bump this file and `VERSION` — see `CONTRIBUTING.md`.

---

## [2.1.0]

### Added
- Three opt-in CI workflows in `global/workflows/`, deployed like the factory workflows (Claude Code target):
  - `secret-scan.yml` — runs `gitleaks` over every push and pull request to catch committed secrets.
  - `check-contradictory-instructions.yml` — heuristically flags pairs of directive-shaped lines in `.github/copilot-instructions.md`, `.github/instructions/`, `CLAUDE.md`, and `AGENTS.md` that assert and then negate the same thing (e.g. "Always use X" / "Never use X").
  - `check-stale-instructions.yml` — flags markdown links and backtick-quoted paths in the same instruction files that point at a file no longer in the repo (deleted or renamed).
  - Both instruction checks are read-only heuristics scoped to the files `TARGETS.md` already documents as instruction sources, so they run as no-ops in a repo (like this one) that doesn't deploy those files, and start finding real issues the moment a project does.

### Why
The factory workflows cover the autonomous loop; most projects adopting this kit want a smaller, unconditional safety net that works without a Claude subscription. Secrets, contradictory rules, and stale file references are the three governance failures a human reviewer is least likely to notice themselves, because none of them produce a build error.

## [2.0.0]

Breaking: output paths changed, and the entry point is now `tooling/aigov.py`. Existing repos move with `python tooling/aigov.py migrate` (once).

### Why
v1 wrote files for every AI tool whether a repo used it or not, and some of those paths aren't read by any tool: prompts went to `.vscode/prompts/*.md` (VS Code reads `.github/prompts/*.prompt.md`), agents went to `.copilot/agents/*.yml` (Copilot reads `.github/agents/*.agent.md`), and `.copilot/mcp.json` isn't read from a repo. It also merged `global/instructions/readme.md` into every generated instructions file and pasted domain overlays into every request.

### Added
- `tooling/aigov.py` with `install`, `sync` (plus `--check` for CI), `migrate`, and `status`.
- **Targets.** Each repo chooses its AI tool(s): `copilot`, `claude-code`, or both. aigov writes only for those tools, only to paths their vendors document. `TARGETS.md` lists every path with a doc link.
- **Refuse, don't guess.** No tool chosen, a file that exists but wasn't written by aigov, a generated file edited by hand, a v1 file whose content doesn't match what v1 wrote: each stops the run before anything is changed. `--force` only ever overrides hand edits to files aigov wrote.
- **Generated-file record.** `.ai-governance.json` now records every file aigov wrote, with a line-ending-insensitive SHA-256. `sync` uses it to remove files you've excluded (closing v1's "doesn't prune" limitation), and `migrate` uses it to delete only what it can prove it wrote.
- `migrate` detects v1 output (by the v1 header or by exact match with the kit source it was copied from), shows what it will replace, and asks for confirmation (`--yes` for scripts).
- Domain overlays for Copilot are written as path-scoped `.github/instructions/<domain>-<name>.instructions.md`. New optional `templates/<Domain>/overlay.json` sets the `applyTo` glob; `templates/UI/overlay.json` scopes the accessibility rules to front-end file types.
- Claude Code gets agents (`.claude/agents/`), commands (`.claude/commands/`), and MCP (`.mcp.json`), converted from the same sources.
- The 1.6.0 `hooks` and `workflows` categories and the factory engine, ported to aigov for the `claude-code` target. Hooks become one generated `.claude/settings.json`; workflows are written to `.github/workflows/` by name; `.factory/` ships when a `factory-*` workflow does. All are recorded like any other generated file, so excluding one now removes it (1.6.0 left the copies behind). `migrate` recognizes 1.6.0 copies of all three.

### Changed
- Copilot outputs: `.github/copilot-instructions.md`, `.github/instructions/`, `.github/prompts/<name>.prompt.md`, `.github/agents/<name>.agent.md`, `.github/skills/<name>/`, `.vscode/mcp.json`.
- Agents in `.yml` are converted to each tool's Markdown agent format; `.agent.md` files are copied as-is for Copilot.
- Prompts get a `description` frontmatter line from their first heading.
- Skills are written once to `.claude/skills/` when a repo uses both tools (Copilot reads that folder too).
- `readme.md` files are never deployed from any category.
- `--output` defaults to the current folder, and aigov refuses to write into the kit itself. The v1 advice to edit `REPO_ROOT` for embedded setups no longer applies.

### Removed
- `.copilot/agents/`, `.copilot/mcp.json`, and `.vscode/prompts/` outputs.
- Merging hook fragments into a hand-written `.claude/settings.json` (1.6.0 behavior). aigov now owns that file and stops if one it didn't write exists; exclude the hooks to keep managing it yourself.
- `--reconfigure` and `--templates` on sync. Use `install` for a new repo, `migrate` to change tools, and edit `templates` in `.ai-governance.json` then `sync` to change overlays.

### Deprecated
- `tooling/sync_configs.py`: now a thin wrapper that runs `aigov.py sync` for v2 repos. Removed in the next major release.

---

## [1.6.0]

### Added
- **`workflows` as a sixth canonical asset category**, alongside `instructions`/`prompts`/`agents`/`skills`/`hooks`. `global/workflows/*.yml` deploys into a target repo's `.github/workflows/`. This is the category for governance that runs **whether or not anyone opens an editor**: `instructions/` is a policy a model reads, `hooks/` is a rule the harness enforces during a session, and a workflow is a rule that runs on a schedule or a webhook with no session involved at all. Deployment is additive and never prunes — a repo's own `ci.yml` beside a deployed `factory-conductor.yml` survives every re-sync untouched.
- **The Factory** — a governed autonomous loop that turns GitHub issues into reviewable pull requests on a Claude subscription's spare capacity, and keeps its own queue fed with scheduled audits. Ships **inert** (`enabled: false`); deploying it starts nothing until a repo writes its own `.factory.json`.
  - `global/workflows/factory-conductor.yml` — hourly cron. Asks the governor for headroom, claims a slot in the ledger, dispatches one worker. Runs no model itself, so a tick costs nothing when the answer is "no headroom".
  - `global/workflows/factory-worker.yml` — runs one issue under a turn allowance and a wall-clock deadline, then opens a pull request or escalates. Never merges, never pushes to the default branch.
  - `global/workflows/factory-audit.yml` — daily cron running read-only audits (security, accessibility, SEO, dependencies, docs drift) whose only output is **issues** filed into the same queue. All five ship disabled.
  - `global/factory/` — the dependency-free Node 20 engine (`ledger.mjs`, `governor.mjs`, `factory.mjs`), deployed to `.factory/` whenever a `factory-*` workflow ships. Stdlib only, deliberately: this code runs with repository credentials on a schedule, and a dependency tree would be the largest thing in it to trust.
  - `global/instructions/05-autonomous-factory.md` — the standing rules for any run nobody is watching (nothing merges itself; every run ends in a pull request or an escalation; budget is a boundary; report honestly about checks that did not run; never weaken a test; stay in scope; record learnings with a confidence mark).
  - `global/skills/factory-task/` and `global/skills/factory-audit/` — the run procedures the worker and auditor follow.
  - `docs/factory-playbook.md` — setup, the dry-run rollout path, governor tuning, task classes, audits, and what to watch for in the first weeks.
- Both engine scripts carry `--self-test`: executable assertions over the admission policy and the execution-log parser, needing no repo, branch, or network. The governor's self-test **is** the specification of the admission policy — change a rule, change its assertion in the same commit.

### Added (self-hosting)
- **This repository now runs its own factory.** Deployed mirrors of the factory assets live at `.github/workflows/factory-*.yml`, `.factory/` and `.claude/skills/factory-*/`, alongside a repo-specific `.factory.json`. Same canonical-source-plus-mirror pattern the kit already uses for `.claude/skills/` — change `global/`, re-deploy, never edit the mirror. Deployed by copying just those paths out of a scratch sync rather than running `sync_configs.py` against the repo root, which would also regenerate `CLAUDE.md`, `.vscode/` and `.copilot/` from the kit's generic instruction set and clobber this repo's own docs.
- Settings chosen for a repo that shares one Claude subscription with another factory and a human: `dry_run: true`, `wip_limit: 1`, `reserve_fraction: 0.5`, and `docs-drift` as the only enabled audit — fitting for a repo that is largely documentation describing its own assets, where a claim and the file it describes drift apart quietly. The governor accounts **per repo**, so two repos each reserving half can still, together, spend more than either number suggests; both start low deliberately.

### Added (the retro reader)
- **`global/workflows/factory-retro.yml` + `global/factory/scripts/retro.mjs`** — a weekly job that joins the ledger with what GitHub says happened to the issues the factory touched, and publishes a report to the job summary plus a 90-day artifact.
- **It reports; it never tunes.** Its permissions are `contents: read` and `issues: read` and nothing else — it cannot edit `.factory.json`, open a pull request, or change a label. This is the one component holding exactly the evidence needed to argue for a bigger budget, more concurrency or another audit, which is precisely why it must not be able to grant any of them: a loop that can widen its own limits on its own evidence has stopped being bounded, and it would do it sincerely. The governor decides what may run, the retro says how that went, and a person moves the numbers between them.
- **Merged, not "pull requests opened", is the headline.** A PR nobody wanted cost exactly what a wanted one cost, so every cost-per-outcome figure divides by human merges, established from the issue timeline (an issue closed as wontfix and one closed by a merged PR are indistinguishable from the issue alone).
- Also reports turns-per-merge **per task class** (the ratio that makes a charter decidable rather than guessed), issues that failed more than once (an underspecified issue, not a weak worker — rewrite it, do not raise a budget at it), audit signal rate as merged ÷ decided, and the share of turns that are **estimated** rather than measured, loudly above 20%, since a budget tuned on guessed turns is tuned on a guess.
- **Unknown is never folded into failure** — an issue GitHub cannot answer for is reported as unknown, because a metric that lies when the API is flaky is worse than no metric. And the report does not file itself as an issue: a weekly report landing in the tracker competes with the queue it reports on.

### Hardened (queue safety)
- **`hold_labels` now match case-insensitively, and an entry ending in `*` matches by prefix.** A repo can have a second automation keyed on a whole label family — HockeyManagerPortal triggers a separate agent pipeline on any `agent:*` label — and the factory admitting such an issue would put two agents on one issue and race them to open competing pull requests, the exact collision that repo's own CLAUDE.md records happening (issues #1548/#1552/#1553). Enumerating every suffix is impossible; `agent*` is not. Case-insensitivity matches how such watchers usually compare labels, so the two agree on what "held" means rather than differing on capitalisation.

### Hardened
- **Billing guard.** `claude-code-action` resolves its key as `inputs.anthropic_api_key || env.ANTHROPIC_API_KEY` (its `action.yml`) — it reads the *environment* when no input is given, and a self-hosted runner inherits its host's environment, where such a key may exist for something unrelated; the action's own setup docs note a static credential takes precedence over other auth. Every model-running factory workflow now pins `ANTHROPIC_API_KEY: ""` at job scope and preflights that `CLAUDE_CODE_OAUTH_TOKEN` is present, failing fast with a clear message rather than starting a run that could authenticate some other way. The conductor carries neither guard because it runs no model.
- **`require_self_hosted`.** Fails a factory job that lands on a GitHub-hosted runner, gating on `runner.environment` (`github-hosted` | `self-hosted`) — for a factory that must run on its owner's hardware and spend no Actions minutes.
- **Host capacity guard** (`global/factory/scripts/hostcheck.mjs`, `host` config block). `wip_limit` counts factory work only; a self-hosted box shares itself with CI, a container swarm, and everything else on it, none of which the factory can see. Load per CPU, available memory and free disk are now asked of the machine, by the conductor before dispatch (avoids admit-then-defer churn) and by the worker before starting (authoritative, since another runner on the same box may have taken the headroom in between). **A busy host defers rather than fails**: the claim is released and the issue requeues with nothing consumed and nothing escalated. Reads `MemAvailable` rather than `MemFree` (page cache is reclaimable; `MemFree` is near zero on a healthy Linux box and would defer every run forever) and `/proc/loadavg` rather than `os.loadavg()` (which returns `[0,0,0]` where there is no load concept, reading as a perfectly idle machine). Any unreadable probe is skipped rather than treated as unhealthy — a guard, not a gate.

### Fixed
- `claim` used the global `deadline_minutes` rather than the task class's own, so a `mechanical` task held a 90-minute WIP slot instead of 30 — a dead run blocked the limit for an extra hour. Found by exercising the ledger against a real git remote.
- A refused claim (WIP full, or already in flight) threw a raw stack trace instead of exiting 1 with a readable message, burying the reason in a failed step.

### Notes
- **There is no public API that reports Claude subscription (Pro/Max) usage**, so the governor cannot poll for headroom. It keeps its own turn ledger and treats a usage-limit error observed by a real run as authoritative over its own arithmetic, falling back to a configured cooldown when a refusal carries no parseable reset time. Turns are a proxy, not a meter — the budgets are dials to calibrate per repo, not physical units.
- `reserve_fraction` (default `0.3`) is the design's central knob: the share of every budget the factory refuses to spend, held back so a human sitting down at a terminal finds headroom rather than a limit the overnight queue already consumed.
- The runner is a repository **variable** (`FACTORY_RUNNER`), not a `.factory.json` key, because `runs-on` is evaluated before any step can read a file. It accepts a JSON string or a JSON array of labels for a self-hosted pool.
- Pattern credit: the **Ember Software Factory** ([jomcgi.dev/slop/factory](https://jomcgi.dev/slop/factory)), which runs a considerably larger version of this loop against a live monorepo and publishes its own numbers. This kit's version is deliberately smaller — GitHub Actions, a branch, and the learnings log the kit already ships, rather than microVMs and a bespoke control plane.

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
