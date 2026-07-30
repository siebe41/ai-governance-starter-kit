
# Enterprise AI Governance & Onboarding Starter Kit

A production-ready reference architecture and modular configuration framework designed for enterprise IT teams to standardize AI rules, prompts, agent roles, and Model Context Protocol (MCP) servers across developer tooling—whether using GitHub Copilot, VS Code, Claude, or custom agent setups.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Architecture](https://img.shields.io/badge/Architecture-Single--Source--of--Truth-orange)
![Protocol](https://img.shields.io/badge/Standard-MCP%20Enabled-green)

---

## 🎯 Purpose & Architecture Overview

This repository operates on a **Single Source of Truth, Multi-Target Deployment** model. Rather than manually copying and maintaining separate AI rules across multiple IDEs or repositories, everything is defined centrally and deployed via automation:


```

```
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
    +------------------------------+------------------------------+
    |                              |                              |
    v                              v                              v

```

+---------------+              +---------------+              +---------------+
|   .github/    |              |   .vscode/    |              |   .copilot/   |
| (Copilot      |              | (Prompts &    |              | (Agent roles  |
|  Instructions)|              |  MCP config)  |              |  & MCP config)|
+---------------+              +---------------+              +---------------+

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
│   └── mcp/                   # mcp-servers.json (Central MCP server registry)
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

📦 Deploying .vscode Configuration...
  [+] Copied VS Code Prompt: code-review.md
  [+] Copied VS Code Prompt: generate-unit-tests.md

📦 Deploying .copilot Configuration...
  [+] Copied Copilot Agent: coordinator.yml
  [+] Copied Copilot Agent: validator.yml

📦 Deploying Global MCP Servers...
  [+] Generated VS Code MCP Config: .vscode/mcp.json
  [+] Generated Copilot Agent MCP Config: .copilot/mcp.json

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
