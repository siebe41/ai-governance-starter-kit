
# Enterprise AI Governance & Onboarding Starter Kit

A production-ready reference architecture and modular configuration framework designed for enterprise IT teams to standardize AI rules, prompts, agent roles, and Model Context Protocol (MCP) servers across developer tooling—whether using GitHub Copilot, VS Code, Claude, or custom agent setups.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Architecture](https://img.shields.io/badge/Architecture-Single--Source--of--Truth-orange)
![Protocol](https://img.shields.io/badge/Standard-MCP%20Enabled-green)

**New here?** → [`QUICKSTART.md`](/QUICKSTART.md) has the fast path for both a technical lead onboarding one project and an IT admin rolling this out org-wide. Proposing a change? → [`CONTRIBUTING.md`](/CONTRIBUTING.md) covers the review bar per path, and [`CHANGELOG.md`](/CHANGELOG.md) / `VERSION` track what's shipped.

---

## 🎯 Purpose & Architecture Overview

This repository operates on a **Single Source of Truth, Multi-Target Deployment** model. You write your AI rules, prompts, agents, skills, and MCP servers once, in `global/`. `tooling/aigov.py` then writes them into each project repo, in the exact place **the AI tool that project uses** reads them from.

```text
          global/  +  templates/<Domain>/  +  the project's local_dirs
                                   |
                        tooling/aigov.py
            (asks which AI tool; writes only for that tool)
                                   |
          +------------------------+------------------------+
          |                                                 |
   GitHub Copilot                                     Claude Code
   .github/copilot-instructions.md                    CLAUDE.md
   .github/instructions/*.instructions.md             .claude/commands/*.md
   .github/prompts/*.prompt.md                        .claude/agents/*.md
   .github/agents/*.agent.md                          .claude/skills/<name>/
   .github/skills/<name>/                             .claude/settings.json (hooks)
   .vscode/mcp.json                                   .mcp.json
                                                      .github/workflows/factory-*.yml
                                                      .factory/  (factory engine)
```

**How aigov decides where things go:** each item goes to the one path its tool documents. Nothing is written for a tool the repo doesn't use, and nothing is written to a path no tool reads. The complete table, with a vendor-doc link for every row, is in [`TARGETS.md`](/TARGETS.md).

**How aigov stays safe:** it never guesses. If a choice hasn't been made, or a run would overwrite or delete a file it can't prove it wrote, it stops, explains why, and changes nothing. Every file it writes is recorded in the project's `.ai-governance.json` with a content fingerprint, and it only ever deletes files on that list that nobody has edited.

---

## 🏗️ Folder Hierarchy

```text
ai-governance-starter-kit/
├── TARGETS.md                 # Exactly where each item lands, per AI tool, and why
├── docs/                      # Governance playbook & architecture diagrams
├── global/                    # 🎯 CANONICAL SINGLE SOURCE OF TRUTH
│   ├── instructions/          # 00-security-governance.md, 01-coding-standards.md, etc.
│   ├── prompts/               # code-review.md, generate-unit-tests.md, ...
│   ├── agents/                # coordinator.yml, plan.yml, ... (or *.agent.md)
│   ├── skills/                # test-driven-development/, learnings-log/, ...
│   ├── hooks/                 # lint-before-finish.json (Claude Code hook fragments)
│   ├── workflows/             # factory-conductor.yml, factory-worker.yml, factory-audit.yml, ...
│   ├── factory/               # the autonomous-factory engine (config + Node scripts)
│   ├── mcp/                   # mcp-servers.json (central MCP server registry)
│   └── LEARNINGS.template.md  # Seed for each repo's mistakes/learnings log
├── templates/                 # 🎨 DOMAIN OVERLAYS (opt-in per repo)
│   └── UI/                    # instructions/a11y.md (WCAG 2.2 AA) + overlay.json (applyTo)
└── tooling/
    ├── aigov.py               # 🛠️ install / sync / migrate / status
    └── sync_configs.py        # Deprecated v1 entry point; forwards to `aigov.py sync`
```

---

## 🏗️ Pre-Onboarding Setup: Fork vs. Subtree

Before onboarding developers, choose how projects get the kit. Either way, aigov reads its sources from the kit folder it lives in and writes into the project you point it at (`--output`, or the current folder). No path editing is needed.

### Option A: Central Standalone Repository (Recommended for Org-Wide Adoption)
Fork or clone this repository to your internal Git server (e.g. `github.com/YOUR_ORG/ai-governance`). IT admins customize `global/`; developers run aigov against their own project repos.

```bash
git clone https://github.com/YOUR_ORG/ai-governance.git
python ai-governance/tooling/aigov.py install --output path/to/your-project
```

### Option B: Embedded Subtree (Recommended for Individual App Repos)

```bash
cd /path/to/your-application-repo
git subtree add --prefix vendor/ai-governance https://github.com/YOUR_ORG/ai-governance.git main --squash
python vendor/ai-governance/tooling/aigov.py install
```

A submodule (`git submodule add ... vendor/ai-governance`) works the same way.

---

## ⚡ Commands

| Command | When | What it does |
| --- | --- | --- |
| `aigov.py install` | Once per repo | Asks which AI tool(s) the repo uses and which domain overlays it wants, then writes only those files. Refuses if the repo is already installed or has v1 files. |
| `aigov.py sync` | Whenever the kit's rules change | Rewrites the same files from the current kit. Never asks questions, so it's safe in CI. Removes files you've since excluded. |
| `aigov.py sync --check` | In CI | Changes nothing; fails if any generated file is out of date or was hand-edited. |
| `aigov.py migrate` | Changing or adding a tool, or moving a v1 repo | Asks for the new tool choice, shows what it will write and remove, asks for confirmation, then does it. |
| `aigov.py status` | Any time | Lists the repo's tools and the state of every file aigov wrote (`ok`, `edited`, `missing`). |

Non-interactive use (CI, scripts): pass the answers as flags, e.g. `install --targets copilot --templates UI` or `migrate --targets copilot claude-code --yes`. Without a terminal and without those flags, aigov refuses rather than assuming.

### What aigov refuses to do

* Run `sync` when no AI tool has been chosen.
* Overwrite a file that exists but wasn't written by aigov (e.g. a hand-written `.github/copilot-instructions.md`). Move or rename it first.
* Overwrite or delete a file aigov wrote that someone has since edited. `--force` discards those edits; it still never touches files aigov didn't write.
* Replace v1 files whose content doesn't match what the v1 kit wrote, unless you pass `--force` after saving anything you need.
* Delete `LEARNINGS.md`, ever.

Every refusal happens before anything is written, so a refused run leaves the repo exactly as it was.

### Example: `install` for a Copilot repo

```text
Which AI tool(s) does this repo use?
  [1] copilot      GitHub Copilot (VS Code, Visual Studio, github.com, Copilot CLI)
  [2] claude-code  Claude Code
  [3] both
Your selection: 1

Domain overlays to add on top of the Global rules:
  [0] none
  [1] UI
Your selection (e.g. '1 2', Enter for none): 1

GitHub Copilot (VS Code, Visual Studio, github.com, Copilot CLI): 65 file(s)
  [+] .github/agents/plan.agent.md
  [+] .github/copilot-instructions.md
  [+] .github/instructions/ui-a11y.instructions.md
  [+] .github/prompts/code-review.prompt.md
  [+] .vscode/mcp.json
  [+] .github/skills/learnings-log/  (1 file)
  ...

Note: Copilot's cloud agent on github.com doesn't read MCP servers from a file. Configure them in the repo's Settings > Copilot > MCP servers.
```

---

## 🧩 Include/Exclude & Bring Your Own

Every project's `.ai-governance.json` holds its choices plus the record of what aigov wrote. Commit it so teammates and CI apply the same selection.

```json
{
  "version": 2,
  "targets": ["copilot"],
  "templates": ["UI"],
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
  },
  "generated": { "...": "written by aigov; don't edit" }
}
```

* **`targets`**: the AI tools this repo uses. Change it with `migrate`, not by hand, so old files get cleaned up.
* **`templates`**: domain overlays. Edit the list and run `sync`.
* **`exclude`**: source filenames to leave out of this repo (folder names for `skills`; filename or stem for `hooks` and `workflows`, e.g. `lint-before-finish`). Edit and run `sync`; files it previously wrote for them are removed. Excluding every `factory-*` workflow also removes the `.factory/` engine.
* **`local_dirs`**: project folders merged in alongside `global/`, so project-specific rules survive kit updates. For `instructions`, this is the project's Repo layer.
* **`generated`**: aigov's record of every file it wrote, with a fingerprint. Don't edit it.

---

## 🧠 Included Skills

`global/skills/` ships agent skills: procedural `SKILL.md` folders that both GitHub Copilot and Claude Code load and self-trigger by description. aigov writes them to `.github/skills/<name>/` for Copilot, `.claude/skills/<name>/` for Claude Code, or once to `.claude/skills/` when a repo uses both (Copilot reads that folder too). Shipped today: a `learnings-log` skill enforcing the Mistakes & Learnings Log protocol below; `ai-team-orchestration` and `acquire-codebase-knowledge` (codebase mapping with a bundled scan script); the `caveman` terse-communication family; three engineering-discipline skills (`test-driven-development`, `using-git-worktrees`, `finishing-a-development-branch`) adapted from [obra/superpowers](https://github.com/obra/superpowers), MIT licensed; and `factory-task`/`factory-audit`, the run procedures behind the autonomous factory below. Full list, usage notes, and how to add your own in [`global/skills/readme.md`](/global/skills/readme.md).

---

## 🪝 Global Hooks

`global/hooks/` ships [Claude Code hook](https://docs.claude.com/en/docs/claude-code/hooks) fragments — the mechanism for turning a "the model should always do X" instruction into something the harness enforces outside model context, rather than something a model has to remember on every turn. Shipped today: `lint-before-finish` (a `Stop` hook that blocks finishing on a dirty tree until `npm run lint` passes). aigov combines the fragments into one generated `.claude/settings.json` (Claude Code target only) and won't merge into a hand-written one — full behavior, the security note on vendoring shell commands, and how to add your own in [`global/hooks/readme.md`](/global/hooks/readme.md).

---

## 🏭 The Autonomous Factory

`global/workflows/` ships GitHub Actions workflows (with the `claude-code` target) that together form a **factory**: a governed loop that turns GitHub issues into reviewable pull requests on whatever capacity a Claude subscription has spare, and keeps its own queue fed with scheduled audits. A conductor cron asks a governor whether there is headroom and dispatches at most a configured number of workers; each worker runs exactly one issue under a turn allowance and a wall-clock deadline, then opens a pull request or escalates to a human. **Nothing merges itself** — the human merge decision is the only review this work gets, and a loop that routed around it would just be an unreviewed commit stream.

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
**change `global/`, then re-deploy; never edit a mirror.** aigov refuses to write into the kit itself, so re-deploy by installing into a scratch folder (`aigov.py install --targets claude-code --templates --output <tmp>`) and copying just those paths back. The `docs-drift` audit
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

`global/workflows/` is the category for governance that runs **whether or not anyone opens an editor** — `instructions/` is a policy a model reads, `hooks/` is a rule the harness enforces during a session, and a workflow is a rule that runs on a schedule or a webhook with no session involved at all. Files deploy into `.github/workflows/` by name: a repo's own `ci.yml` beside a deployed `factory-conductor.yml` is never touched, and only the files aigov wrote are ever removed (when you exclude them).

Like `hooks/`, this category's assets **execute** — here with repository credentials and a `permissions` block — so read any workflow in full before vendoring it. See [`global/workflows/readme.md`](/global/workflows/readme.md) for the security notes and how to add your own.

---

## 🔌 Global MCP Integration

MCP server definitions live in `global/mcp/mcp-servers.json`. aigov writes them to `.vscode/mcp.json` for Copilot in VS Code and `.mcp.json` for Claude Code. Copilot's cloud agent on github.com reads MCP servers from the repo's **Settings > Copilot > MCP servers** page instead of a file, so that one step is manual.

Keep secrets out of the file by using environment-variable placeholders. aigov copies values exactly as written, and the placeholder syntax differs between tools, so write them in the form your tools expect (see [`TARGETS.md`](/TARGETS.md)).

**`graft`** ([trailhq/Graft](https://github.com/trailhq/Graft), published as `@nanonets/graft`, MIT) is a codebase-context server: it serves a local, tree-sitter-built knowledge graph of a repo to any MCP-capable agent. It needs no secret and calls no external service by default — evaluated and vendored on that basis (see `CHANGELOG.md`). The entry alone only makes the tool *available*; it does nothing in a project until a developer opts in by running `npx graft init` there once, which builds the local graph and (on Claude Code) additionally wires its own skill, hooks, and statusline — none of which this kit vendors, since `graft init` manages that file directly. It's a heavier, LLM-optional alternative to `global/skills/acquire-codebase-knowledge/`'s stdlib-only scan — reach for `acquire-codebase-knowledge` when you want a zero-dependency one-time snapshot, and `graft` when you want a living, auto-refreshing graph with deeper agent integration.

---

## 🧩 Included Workflow Methodologies

Beyond the baseline security/coding/testing guardrails, `global/agents/` and `global/prompts/` package a few opt-in agentic workflow patterns engineers get through aigov (and can drop with `exclude`) or by wiring the prompt/agent file into their tool of choice:

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

* On install, `global/LEARNINGS.template.md` is seeded as `LEARNINGS.md` at the project root, only if it doesn't exist. aigov never tracks, overwrites, or deletes it, so accumulated entries survive every sync and migration.
* Entries follow a fixed `Context` / `Mistake / Gotcha` / `Correct Pattern` format, kept short enough to act as a pre-flight checklist rather than a changelog.
* On Claude Code, `global/skills/learnings-log/` enforces this as a self-triggering Skill (fires at task start and right after a correction) instead of relying on the instructions file being noticed inside a large concatenated instructions file.

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
