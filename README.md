
# Enterprise AI Governance & Onboarding Starter Kit

A production-ready reference architecture and modular configuration framework designed for enterprise IT teams to standardize AI rules, prompts, agent roles, and Model Context Protocol (MCP) servers across developer tooling—whether using GitHub Copilot, VS Code, Claude, or custom agent setups.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Architecture](https://img.shields.io/badge/Architecture-Single--Source--of--Truth-orange)
![Protocol](https://img.shields.io/badge/Standard-MCP%20Enabled-green)

**New here?** → [`QUICKSTART.md`](/QUICKSTART.md) has the fast path for both a technical lead onboarding one project and an IT admin rolling this out org-wide. Proposing a change? → [`CONTRIBUTING.md`](/CONTRIBUTING.md) covers the review bar per path, and [`CHANGELOG.md`](/CHANGELOG.md) / `VERSION` track what's shipped.

---

## 🎯 Purpose & Architecture Overview

This repository operates on a **Single Source of Truth, Multi-Target Deployment** model. Rather than manually copying and maintaining separate AI rules across multiple IDEs or repositories, everything is defined centrally and deployed via automation:


```

```text
                  +----------------------------------+
                  |   global/ (Canonical Source)     |
                  |  ├── instructions/               |
                  |  ├── prompts/                    |
                  |  ├── agents/                     |
                  |  ├── skills/                     |
                  |  ├── hooks/                      |
                  |  ├── workflows/                  |
                  |  ├── factory/                    |
                  |  └── mcp/                        |
                  +----------------+-----------------+
                                   |
                                   v
                  +----------------------------------+
                  |   templates/ (Domain Overlays)   |
                  |  ├── Cloud/                      |
                  |  ├── UI/                         |
                  |  └── DevOps/                     |
                  +----------------+-----------------+
                                   |
                                   v
                  +----------------------------------+
                  |   tooling/sync_configs.py        |
                  +----------------+-----------------+
                                   |
    +------------------+------------------+------------------+------------------+
    |                  |                  |                  |                  |
    v                  v                  v                  v

+---------------+  +---------------+  +---------------+  +---------------+
|   .github/    |  |   CLAUDE.md   |  |   .vscode/    |  |   .copilot/   |
| (Copilot      |  |  .claude/     |  | (Prompts &    |  | (Agent roles  |
|  Instructions |  |  skills/      |  |  MCP config)  |  | & MCP config) |
|  + workflows/)|  |  settings.json|  |               |  |               |
|   .factory/   |  |  (hooks)      |  |               |  |               |
+---------------+  +---------------+  +---------------+  +---------------+

Every deploy is governed by a per-repo `.ai-governance.json`: which domain
templates are active, which individual files are excluded, and which
project-local folders are merged in as "bring your own" additions. See
"Include/Exclude & Bring Your Own" below.
```

---

## 🏗️ Folder Hierarchy


```

ai-governance-starter-kit/
├── docs/                      # Governance playbook & architecture diagrams
│   ├── governance-playbook.md
│   └── architecture-diagrams.md
│
├── global/                    # 🎯 CANONICAL SINGLE SOURCE OF TRUTH
│   ├── instructions/          # 00-security-governance.md, 01-coding-standards.md, etc.
│   ├── prompts/               # code-review.md, generate-unit-tests.md, refactor.md
│   ├── agents/                # coordinator.yml, validator.yml, researcher.yml
│   ├── skills/                # test-driven-development/, using-git-worktrees/, ...
│   ├── hooks/                 # lint-before-finish.json (Stop/PostToolUse hook fragments)
│   ├── workflows/             # factory-conductor.yml, factory-worker.yml, factory-audit.yml
│   ├── factory/               # the autonomous-factory engine (config + Node scripts)
│   ├── mcp/                   # mcp-servers.json (Central MCP server registry)
│   └── LEARNINGS.template.md  # Seed file for the per-repo mistakes/learnings log
│
├── templates/                 # 🎨 DOMAIN-SPECIFIC OVERLAYS
│   ├── UI/                    # Populated: instructions/a11y.md (WCAG 2.2 AA)
│   ├── Cloud/                 # Not yet populated — pattern only
│   └── DevOps/                # Not yet populated — pattern only
│
└── tooling/                   # 🛠️ DEPLOYMENT ENGINE
└── sync_configs.py        # Python sync engine (interactive menu & CLI)

```

---

## 🏗️ Pre-Onboarding Setup: Fork vs. Subtree

Before onboarding developers to use this toolset, your organization should choose how to integrate this repository into your development lifecycle:

### Option A: Central Standalone Repository (Recommended for Org-Wide Adoption)
Fork or clone this repository to a central location on your internal Git server (e.g., `github.com/YOUR_ORG/ai-governance`). IT admins customize the global security rules, and developers run the sync script to generate local tooling configs across their projects.

```bash
git clone [https://github.com/YOUR_ORG/ai-governance.git](https://github.com/YOUR_ORG/ai-governance.git)
cd ai-governance

```

### Option B: Embedded Sub-Repository / Subtree (Recommended for Individual App Repos)

Embed this kit directly into an existing application repository so governance rules travel alongside source code.

#### Git Subtree Method (Recommended):

```bash
cd /path/to/your-application-repo
git subtree add --prefix vendor/ai-governance [https://github.com/Siebe41/ai-governance-starter-kit.git](https://github.com/Siebe41/ai-governance-starter-kit.git) main --squash

```

#### Git Submodule Method:

```bash
git submodule add [https://github.com/Siebe41/ai-governance-starter-kit.git](https://github.com/Siebe41/ai-governance-starter-kit.git) vendor/ai-governance

```

> **Note for Embedded Setups:** If embedded as a sub-folder (e.g., `vendor/ai-governance/`), update `REPO_ROOT` inside `tooling/sync_configs.py` so output files write to your parent repository root:
> ```python
> REPO_ROOT = SCRIPT_DIR.parent.parent.parent
> 
> ```
> 
> 

---

## ⚡ Developer Onboarding & Deployment

Once configured by your admin team, onboarding a developer is as simple as running the deployment engine.

### Option 1: Interactive Onboarding Menu (Recommended)

Run the script without arguments to open an interactive selection menu where developers can pick domain overlays matching their current tasks:

```bash
python tooling/sync_configs.py

```

**Interactive Example:**

```text
========================================================
 🛠️  AI Configuration Deployment Menu
========================================================

Available Domain Templates:
  [0] None (Deploy Global configuration only)
  [1] Cloud
  [2] DevOps
  [3] UI

Select templates to overlay on top of Global.
  • Enter numbers separated by spaces or commas (e.g. '1, 3' or '1 2')
  • Press ENTER or type '0' for Global only

Your selection: 1, 3

🚀 Starting AI Configuration Sync...
📍 Target Output: /workspace/your-project
🎨 Selected Templates: Cloud, UI

📦 Deploying .github Configuration...
  [+] Generated: .github/copilot-instructions.md

📦 Deploying Claude Code Configuration...
  [+] Generated: CLAUDE.md

📦 Deploying .vscode Configuration...
  [+] Copied VS Code Prompt: code-review.md
  [+] Copied VS Code Prompt: generate-unit-tests.md

📦 Deploying .copilot Configuration...
  [+] Copied Copilot Agent: coordinator.yml
  [+] Copied Copilot Agent: validator.yml

📦 Deploying Claude Skills...
  [+] Copied Claude Skill: test-driven-development/
  [+] Copied Claude Skill: using-git-worktrees/

📦 Deploying Claude Code Hooks...
  [+] Merged hook into .claude/settings.json — Stop: lint-before-finish

📦 Deploying Global MCP Servers...
  [+] Generated VS Code MCP Config: .vscode/mcp.json
  [+] Generated Copilot Agent MCP Config: .copilot/mcp.json

📦 Seeding Learnings Log...
  [+] Seeded: LEARNINGS.md
  [+] Saved selection to .ai-governance.json — edit `exclude` to drop individual assets, or `local_dirs` to add your own, then re-run the sync.

✅ AI Configuration Sync Completed Successfully!

```

---

### Option 2: Command Line (Automation & CI/CD)

Bypass the interactive menu during automated setups or CI/CD pipelines using CLI flags:

```bash
# 1. Deploy Global rules ONLY (no domain overlays)
python tooling/sync_configs.py --templates

# 2. Deploy Global + Cloud domain overlay
python tooling/sync_configs.py --templates Cloud

# 3. Deploy Global + multiple domain overlays (Cloud and UI)
python tooling/sync_configs.py --templates Cloud UI

# 4. Output configs directly into a specific project directory
python tooling/sync_configs.py --templates Cloud DevOps --output /path/to/target-repo

```

---

## 🧩 Include/Exclude & Bring Your Own

Domain templates (`--templates Cloud UI`) select whole bundles. For finer control — dropping one instruction, prompt, agent, or skill you don't want, or adding your own without touching the vendored kit — every sync writes a `.ai-governance.json` at the target repo root and reads it back on the next run:

```json
{
  "version": 1,
  "templates": ["Cloud"],
  "exclude": {
    "instructions": [],
    "prompts": ["caveman-mode.md"],
    "agents": ["ralph-swarm-runner.yml"],
    "skills": [],
    "hooks": [],
    "workflows": []
  },
  "local_dirs": {
    "instructions": ["governance-local/instructions"],
    "prompts": [],
    "agents": [],
    "skills": ["governance-local/skills"],
    "hooks": [],
    "workflows": []
  }
}
```

* **`exclude`** — filenames (or, for `skills`, folder names; for `hooks`, the fragment's filename stem, e.g. `lint-before-finish`; for `workflows`, either the filename or its stem) to skip on every future sync. Excluding every `factory-*` workflow also suppresses the `.factory/` engine, so a repo that doesn't want a factory gets no orphaned engine directory either. Nothing here is deleted from `global/`; it's just not deployed to *this* project. Edit the list, re-run `python tooling/sync_configs.py` (no flags needed — it reuses this file), done.
* **`local_dirs`** — extra folders, relative to your project root, merged in alongside the canonical `global/` assets for each category. Drop a `governance-local/instructions/04-team-conventions.md` or `governance-local/skills/my-skill/SKILL.md` in your own project, list the parent folder here, and it deploys on every sync exactly like a canonical asset — including through `--exclude` if you ever want to turn it off. Because these files live outside the vendored `vendor/ai-governance/` (or wherever you cloned the kit), they survive `git subtree pull`/`submodule update` without merge conflicts. `hooks` fragments deploy the same way, except the target is a merge into `.claude/settings.json` rather than a directory copy — see [`global/hooks/readme.md`](/global/hooks/readme.md) for exactly how that merge behaves and why excluding a hook doesn't retroactively strip it from a `settings.json` a previous sync already wrote to (same "Known limitation" as below).
* **`--reconfigure`** — ignore a saved `.ai-governance.json` and re-run template selection from scratch (also resets `exclude`/`local_dirs` to empty; hand-edit them back in if you still want them).
* Passing `--templates` explicitly on the command line always wins over a saved selection, for CI/automation use.

**Known limitation:** excluding something already deployed doesn't retroactively delete the file a previous sync wrote (e.g. a `.copilot/agents/*.yml` you previously synced) — the tool only adds/updates, it doesn't prune. Remove the stale file by hand once after changing `exclude`.

`.ai-governance.json` is project configuration, not a build artifact — commit it in your project so teammates and CI apply the same selection.

---

## 🧠 Included Skills

`global/skills/` ships [Claude Code Skills](https://github.com/obra/superpowers) — procedural `SKILL.md` files Claude Code loads and self-triggers by description, deployed to `.claude/skills/<name>/`. Shipped today: a `learnings-log` skill enforcing the Mistakes & Learnings Log protocol below; `ai-team-orchestration` and `acquire-codebase-knowledge` (codebase mapping with a bundled scan script); the `caveman` terse-communication family; three engineering-discipline skills (`test-driven-development`, `using-git-worktrees`, `finishing-a-development-branch`) adapted from `obra/superpowers`, MIT licensed; and `factory-task`/`factory-audit`, the run procedures behind the autonomous factory below. Full list, usage notes, and how to add your own in [`global/skills/readme.md`](/global/skills/readme.md).

---

## 🪝 Global Hooks

`global/hooks/` ships [Claude Code hook](https://docs.claude.com/en/docs/claude-code/hooks) fragments — the mechanism for turning a "the model should always do X" instruction into something the harness enforces outside model context, rather than something a model has to remember on every turn. Shipped today: `lint-before-finish` (a `Stop` hook that blocks finishing on a dirty tree until `npm run lint` passes). Unlike every other category, deployment here is a merge into a target repo's `.claude/settings.json` rather than a directory copy — full behavior, the security note on vendoring shell commands, and how to add your own in [`global/hooks/readme.md`](/global/hooks/readme.md).

---

## 🏭 The Autonomous Factory

`global/workflows/` ships three GitHub Actions workflows that together form a **factory**: a governed loop that turns GitHub issues into reviewable pull requests on whatever capacity a Claude subscription has spare, and keeps its own queue fed with scheduled audits. A conductor cron asks a governor whether there is headroom and dispatches at most a configured number of workers; each worker runs exactly one issue under a turn allowance and a wall-clock deadline, then opens a pull request or escalates to a human. **Nothing merges itself** — the human merge decision is the only review this work gets, and a loop that routed around it would just be an unreviewed commit stream.

The governor is the interesting part, and it exists because **there is no public API that reports Claude subscription (Pro/Max) usage** — the Admin API's usage and cost reports are organisation-scoped and need an Admin API key. So it keeps its own turn ledger on an orphan branch and treats a usage-limit error observed by a real run as authoritative over its own arithmetic. Its central knob is `reserve_fraction`: the share of every budget the factory refuses to spend, held back so that sitting down at a terminal in the evening finds headroom waiting rather than a limit the overnight queue already consumed. The factory is meant to use idle capacity, not to race its owner for it.

### This repository runs its own factory

The kit is not just the source of the factory — it is a customer of it. This repo
carries its own deployed copy:

| Path | What it is |
| :--- | :--- |
| `.github/workflows/factory-*.yml` | mirror of `global/workflows/` |
| `.factory/` | mirror of `global/factory/` |
| `.claude/skills/factory-*/` | mirror of those two skills in `global/skills/` |
| `.factory.json` | this repo's own settings — **not** a mirror |

Same canonical-source-plus-mirror pattern as `.claude/skills/` everywhere else:
**change `global/`, then re-deploy; never edit a mirror.** The `docs-drift` audit
is the one enabled here, which is fitting — a repo that is mostly documentation
about its own assets is exactly where a claim and the file it describes drift
apart quietly.

It runs with `dry_run: true`, `wip_limit: 1` and `reserve_fraction: 0.5` on a
self-hosted runner. The budget is deliberately below what a single repo would
take, because the governor accounts **per repo**: two repos each reserving half
still leaves the pair able to spend more than either number suggests.

The whole thing ships **inert** (`enabled: false`) — deploying it starts nothing until a repo writes its own `.factory.json`. Setup, the dry-run rollout path, tuning, audits, and what to watch for in the first weeks: [`docs/factory-playbook.md`](/docs/factory-playbook.md). Category docs: [`global/workflows/readme.md`](/global/workflows/readme.md) and [`global/factory/readme.md`](/global/factory/readme.md).

---

## ⚙️ Global Workflows

`global/workflows/` is the category for governance that runs **whether or not anyone opens an editor** — `instructions/` is a policy a model reads, `hooks/` is a rule the harness enforces during a session, and a workflow is a rule that runs on a schedule or a webhook with no session involved at all. Files deploy into `.github/workflows/` additively: a repo's own `ci.yml` beside a deployed `factory-conductor.yml` survives every re-sync untouched, and nothing is ever pruned.

Like `hooks/`, this category's assets **execute** — here with repository credentials and a `permissions` block — so read any workflow in full before vendoring it. See [`global/workflows/readme.md`](/global/workflows/readme.md) for the security notes and how to add your own.

---

## 🔌 Global MCP Integration

Model Context Protocol (MCP) server definitions are centrally managed in `global/mcp/mcp-servers.json`. During synchronization, the script formats and deploys these definitions directly into `.vscode/mcp.json` and `.copilot/mcp.json`.

Secrets (e.g., Azure DevOps PATs or GitHub Tokens) are injected using standard environment variable placeholders (e.g., `${AZURE_DEVOPS_PAT}`), keeping credentials safely out of source control.

**`graft`** ([trailhq/Graft](https://github.com/trailhq/Graft), published as `@nanonets/graft`, MIT) is a codebase-context server: it serves a local, tree-sitter-built knowledge graph of a repo to any MCP-capable agent. It needs no secret and calls no external service by default — evaluated and vendored on that basis (see `CHANGELOG.md`). The entry alone only makes the tool *available*; it does nothing in a project until a developer opts in by running `npx graft init` there once, which builds the local graph and (on Claude Code) additionally wires its own skill, hooks, and statusline — none of which this kit vendors, since `graft init` manages that file directly. It's a heavier, LLM-optional alternative to `global/skills/acquire-codebase-knowledge/`'s stdlib-only scan — reach for `acquire-codebase-knowledge` when you want a zero-dependency one-time snapshot, and `graft` when you want a living, auto-refreshing graph with deeper agent integration.

---

## 🧩 Included Workflow Methodologies

Beyond the baseline security/coding/testing guardrails, `global/agents/` and `global/prompts/` package a few opt-in agentic workflow patterns engineers can select via the sync menu or by wiring the prompt/agent file into their tool of choice:

| Methodology | Type | File | Summary |
| :--- | :--- | :--- | :--- |
| **Ralph Wiggum** | Agent | `global/agents/ralph-wiggum.yml` | Solo autonomous loop-driven builder, based on the [Ralph Wiggum technique](https://github.com/fstandhartinger/ralph-wiggum): each invocation reads specs, implements one task, verifies acceptance criteria, commits, and signals `<promise>DONE</promise>`. |
| **Swarm** | Agents | `global/agents/foreman.yml`, `swarm-scout.yml`, `swarm-builder.yml`, `swarm-auditor.yml` | Foreman decomposes a feature into independent, non-overlapping units of work and dispatches each to a Scout (research), Builder (implement), or Auditor (review/test) sub-agent running in its own branch/worktree; Foreman owns the merge. |
| **Ralph Swarm** | Agents | `global/agents/foreman.yml`, `global/agents/ralph-swarm-runner.yml` | Foreman partitions a large `IMPLEMENTATION_PLAN.md` across several parallel Ralph loops; each Runner claims tasks off the shared plan to avoid collisions, and the Foreman reconciles/merges as runners signal done. |
| **AI Team** | Agents / Skill | `global/agents/ai-team-producer.yml`, `ai-team-dev.yml`, `ai-team-qa.yml`, `global/skills/ai-team-orchestration/` | A small persistent team (Producer coordinates + merges, Dev implements, QA optionally tests) running Plan → Implement → Test → optional review/QA → Merge, with a project brief and sprint-plan template for durable cross-session context. |
| **Autonomous Factory** | Workflows / Skills | `global/workflows/factory-*.yml`, `global/factory/`, `global/skills/factory-task/`, `factory-audit/` | A governed unattended loop: a cron conductor admits queued GitHub issues within a usage budget, each worker runs one issue under a turn/time cap and opens a PR or escalates, and scheduled read-only audits file new work into the same queue. Nothing merges itself. See [`docs/factory-playbook.md`](/docs/factory-playbook.md). |
| **Spec-Driven Development** | Prompt | `global/prompts/spec-driven-development.md` | Specify → Plan → Tasks → Implement workflow (in the spirit of GitHub's Spec Kit) — the spec stays the source of truth throughout implementation. |
| **Caveman Mode** | Prompt / Skill | `global/prompts/caveman-mode.md`, `global/skills/caveman/` (+ `caveman-commit`, `caveman-review`, `caveman-help`, `compress`) | Optional terse, low-token communication style — never applied to code correctness or user-facing deliverables. The `global/skills/` family self-triggers on Claude Code with commit/review/compress variants; the prompt covers Copilot/VS Code, which have no Skills system to self-trigger from. |

**Suggested order for a new feature:** run **Plan** or **Spec-Driven Development** to produce a strategy (and, for Spec-Driven, `specs/` + `IMPLEMENTATION_PLAN.md`) → hand that to **Ralph** (small, sequential plans), **Ralph Swarm** (large plans with independent tasks), **Foreman + Scout/Builder/Auditor** (work that splits by function), or the **AI Team** (a persistent team for a whole feature or project) to implement → layer **Caveman Mode** on top of any of them if you want terser status narration along the way.

Step-by-step usage instructions (setup, invocation, and when to prefer which pattern) live in [`global/agents/readme.md`](/global/agents/readme.md) and [`global/prompts/readme.md`](/global/prompts/readme.md) — this table is the index, not the how-to.

---

## 🧠 Mistakes & Learnings Log

`global/instructions/03-learnings-log.md` requires AI assistants to read a per-repo `LEARNINGS.md` file before starting work, and to append to it whenever they're corrected or hit a non-obvious gotcha — so the same mistake never has to be corrected twice.

* On sync, `global/LEARNINGS.template.md` is seeded as `LEARNINGS.md` at the target repo root — but only if that file doesn't already exist, so accumulated entries survive re-syncs.
* Entries follow a fixed `Context` / `Mistake / Gotcha` / `Correct Pattern` format, kept short enough to act as a pre-flight checklist rather than a changelog.
* On Claude Code, `global/skills/learnings-log/` enforces this as a self-triggering Skill (fires at task start and right after a correction) instead of relying on the instructions file being noticed inside a large concatenated `CLAUDE.md`.

---

## 📚 Community & Presentation Resources

* 📜 **[Governance Playbook](/docs/governance-playbook.md):** Security policies, data tiering, and operational checklists.
* 📐 **[Architecture Reference](/docs/architecture-diagrams.md):** Visual Mermaid diagrams for enterprise gateway and agent routing.

---

## 🤝 Contributing & Feedback

Contributions, issue reports, and template expansion ideas are welcome! Open an issue or discussion thread on GitHub.

---

**License:** MIT

**Author:** Andrew J. Siebert ([@Siebe41](https://github.com/Siebe41))

```
