
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
| (Copilot      |  | (Claude Code /|  | (Prompts &    |  | (Agent roles  |
|  Instructions)|  |  Agent SDK)   |  |  MCP config)  |  | & MCP config) |
+---------------+  +---------------+  +---------------+  +---------------+
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
│   ├── mcp/                   # mcp-servers.json (Central MCP server registry)
│   └── LEARNINGS.template.md  # Seed file for the per-repo mistakes/learnings log
│
├── templates/                 # 🎨 DOMAIN-SPECIFIC OVERLAYS
│   ├── Cloud/                 # Cloud/Azure-specific rules and prompts
│   ├── UI/                    # Frontend/UI-specific rules and prompts
│   └── DevOps/                # Pipeline/CI-CD specific rules and prompts
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

📦 Deploying Global MCP Servers...
  [+] Generated VS Code MCP Config: .vscode/mcp.json
  [+] Generated Copilot Agent MCP Config: .copilot/mcp.json

📦 Seeding Learnings Log...
  [+] Seeded: LEARNINGS.md

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
| **Spec-Driven Development** | Prompt | `global/prompts/spec-driven-development.md` | Specify → Plan → Tasks → Implement workflow (in the spirit of GitHub's Spec Kit) — the spec stays the source of truth throughout implementation. |
| **Caveman Mode** | Prompt | `global/prompts/caveman-mode.md` | Optional terse, low-token communication style (lite/default/ultra) for an assistant's own interim narration — never applied to code correctness or user-facing deliverables. |

**Suggested order for a new feature:** run **Spec-Driven Development** to produce `specs/` + `IMPLEMENTATION_PLAN.md` → hand that to **Ralph** (small, sequential plans), **Ralph Swarm** (large plans with independent tasks), or **Foreman + Scout/Builder/Auditor** (work that splits by function rather than by task) to implement → layer **Caveman Mode** on top of any of them if you want terser status narration along the way.

Step-by-step usage instructions (setup, invocation, and when to prefer which pattern) live in [`global/agents/readme.md`](/global/agents/readme.md) and [`global/prompts/readme.md`](/global/prompts/readme.md) — this table is the index, not the how-to.

---

## 🧠 Mistakes & Learnings Log

`global/instructions/03-learnings-log.md` requires AI assistants to read a per-repo `LEARNINGS.md` file before starting work, and to append to it whenever they're corrected or hit a non-obvious gotcha — so the same mistake never has to be corrected twice.

* On sync, `global/LEARNINGS.template.md` is seeded as `LEARNINGS.md` at the target repo root — but only if that file doesn't already exist, so accumulated entries survive re-syncs.
* Entries follow a fixed `Context` / `Mistake / Gotcha` / `Correct Pattern` format, kept short enough to act as a pre-flight checklist rather than a changelog.

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
