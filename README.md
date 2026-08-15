
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
|  Instructions)|  |  skills/      |  |  MCP config)  |  | & MCP config) |
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
    "skills": []
  },
  "local_dirs": {
    "instructions": ["governance-local/instructions"],
    "prompts": [],
    "agents": [],
    "skills": ["governance-local/skills"]
  }
}
```

* **`exclude`** — filenames (or, for `skills`, folder names) to skip on every future sync. Nothing here is deleted from `global/`; it's just not deployed to *this* project. Edit the list, re-run `python tooling/sync_configs.py` (no flags needed — it reuses this file), done.
* **`local_dirs`** — extra folders, relative to your project root, merged in alongside the canonical `global/` assets for each category. Drop a `governance-local/instructions/04-team-conventions.md` or `governance-local/skills/my-skill/SKILL.md` in your own project, list the parent folder here, and it deploys on every sync exactly like a canonical asset — including through `--exclude` if you ever want to turn it off. Because these files live outside the vendored `vendor/ai-governance/` (or wherever you cloned the kit), they survive `git subtree pull`/`submodule update` without merge conflicts.
* **`--reconfigure`** — ignore a saved `.ai-governance.json` and re-run template selection from scratch (also resets `exclude`/`local_dirs` to empty; hand-edit them back in if you still want them).
* Passing `--templates` explicitly on the command line always wins over a saved selection, for CI/automation use.

**Known limitation:** excluding something already deployed doesn't retroactively delete the file a previous sync wrote (e.g. a `.copilot/agents/*.yml` you previously synced) — the tool only adds/updates, it doesn't prune. Remove the stale file by hand once after changing `exclude`.

`.ai-governance.json` is project configuration, not a build artifact — commit it in your project so teammates and CI apply the same selection.

---

## 🧠 Included Skills

`global/skills/` ships [Claude Code Skills](https://github.com/obra/superpowers) — procedural `SKILL.md` files Claude Code loads and self-triggers by description, deployed to `.claude/skills/<name>/`. Shipped today: a `learnings-log` skill enforcing the Mistakes & Learnings Log protocol below; `ai-team-orchestration` and `acquire-codebase-knowledge` (codebase mapping with a bundled scan script); the `caveman` terse-communication family; and three engineering-discipline skills (`test-driven-development`, `using-git-worktrees`, `finishing-a-development-branch`) adapted from `obra/superpowers`, MIT licensed. Full list, usage notes, and how to add your own in [`global/skills/readme.md`](/global/skills/readme.md).

---

## 🔌 Global MCP Integration

Model Context Protocol (MCP) server definitions are centrally managed in `global/mcp/mcp-servers.json`. During synchronization, the script formats and deploys these definitions directly into `.vscode/mcp.json` and `.copilot/mcp.json`.

Secrets (e.g., Azure DevOps PATs or GitHub Tokens) are injected using standard environment variable placeholders (e.g., `${AZURE_DEVOPS_PAT}`), keeping credentials safely out of source control.

---

## 🧩 Included Workflow Methodologies

Beyond the baseline security/coding/testing guardrails, `global/agents/` and `global/prompts/` package a few opt-in agentic workflow patterns engineers can select via the sync menu or by wiring the prompt/agent file into their tool of choice:

| Methodology | Type | File | Summary |
| :--- | :--- | :--- | :--- |
| **Ralph Wiggum** | Agent | `global/agents/ralph-wiggum.yml` | Solo autonomous loop-driven builder, based on the [Ralph Wiggum technique](https://github.com/fstandhartinger/ralph-wiggum): each invocation reads specs, implements one task, verifies acceptance criteria, commits, and signals `<promise>DONE</promise>`. |
| **Swarm** | Agents | `global/agents/foreman.yml`, `swarm-scout.yml`, `swarm-builder.yml`, `swarm-auditor.yml` | Foreman decomposes a feature into independent, non-overlapping units of work and dispatches each to a Scout (research), Builder (implement), or Auditor (review/test) sub-agent running in its own branch/worktree; Foreman owns the merge. |
| **Ralph Swarm** | Agents | `global/agents/foreman.yml`, `global/agents/ralph-swarm-runner.yml` | Foreman partitions a large `IMPLEMENTATION_PLAN.md` across several parallel Ralph loops; each Runner claims tasks off the shared plan to avoid collisions, and the Foreman reconciles/merges as runners signal done. |
| **AI Team** | Agents / Skill | `global/agents/ai-team-producer.yml`, `ai-team-dev.yml`, `ai-team-qa.yml`, `global/skills/ai-team-orchestration/` | A small persistent team (Producer coordinates + merges, Dev implements, QA optionally tests) running Plan → Implement → Test → optional review/QA → Merge, with a project brief and sprint-plan template for durable cross-session context. |
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
