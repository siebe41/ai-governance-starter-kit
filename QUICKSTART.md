# Quickstart

Two paths, depending on who you are. Both take a few minutes.

---

## Technical Lead: onboard one project

1. **Bring the kit into your project** (pick one; see the main `README.md` for the tradeoffs):
   ```bash
   git subtree add --prefix vendor/ai-governance https://github.com/YOUR_ORG/ai-governance-starter-kit.git main --squash
   ```
2. **Install** from your project root:
   ```bash
   python vendor/ai-governance/tooling/aigov.py install
   ```
   It asks two questions: which AI tool the repo uses (GitHub Copilot, Claude Code, or both) and which domain overlays you want. It writes only that tool's files, to the paths in [`TARGETS.md`](/TARGETS.md), and lists every file it wrote.
3. **Commit the generated files** (see "What to Commit" below).
4. Open your editor, Copilot Chat, or Claude Code. The rules, prompts, agents, and skills are live.

**Kit updated?** Run `python vendor/ai-governance/tooling/aigov.py sync`. It reuses your answers and never asks questions.

**Switching tools, or adding a second one?** Run `aigov.py migrate`. It shows what it will write and remove, asks you to confirm, and never deletes a file someone edited.

**Don't want everything?** Add source filenames to `exclude` in `.ai-governance.json` (e.g. `"prompts": ["caveman-mode.md"]`) and run `sync`; the files it wrote for them are removed. To add your own rules or skills without editing the vendored kit, put them in a project folder (e.g. `governance-local/instructions/`) and list it under `local_dirs`.

**Coming from v1** (`sync_configs.py`)? Run `aigov.py migrate` once. It checks that each old file is really one the v1 kit wrote before replacing it, and stops if any were edited.

---

## IT Admin: roll this out org-wide

1. Fork this repo to your org's Git server.
2. Edit `global/instructions/`, `global/prompts/`, `global/agents/`, and `global/mcp/mcp-servers.json` to match your org's actual policies — the shipped content is a working example, not a finished policy.
3. Add a `CODEOWNERS` file to enforce the review bar described in `CONTRIBUTING.md` (governance sign-off required for `global/instructions/` and `global/mcp/`).
4. Populate `templates/<Domain>/` for any domain overlays your org needs (Cloud, UI, DevOps, ...) — the kit ships the pattern, not populated content, since it's org- and stack-specific.
5. Bump `VERSION` and add a `CHANGELOG.md` entry for every change, so project teams can tell whether they're on the latest rules — every generated instructions file is stamped with the version it came from, and `aigov.py status` shows which version wrote a repo's files.
6. Point every project at your fork (see "Pre-Onboarding Setup: Fork vs. Subtree" in the main `README.md`) and make `python tooling/aigov.py install` part of new-project onboarding. Add `aigov.py sync --check` to CI to catch repos that fall behind or get hand-edited.

---

## What Gets Generated

Only the files for the AI tool(s) you chose. [`TARGETS.md`](/TARGETS.md) has the full table with a vendor-doc link per row. In short:

| Tool | Files |
| :--- | :--- |
| GitHub Copilot | `.github/copilot-instructions.md`, `.github/instructions/`, `.github/prompts/`, `.github/agents/`, `.github/skills/`, `.vscode/mcp.json` |
| Claude Code | `CLAUDE.md`, `.claude/commands/`, `.claude/agents/`, `.claude/skills/`, `.mcp.json` |
| Always | `.ai-governance.json` (your choices + record of generated files), `LEARNINGS.md` (seeded once, never overwritten or deleted) |

---

## What to Commit

**In your project** (the sync target): commit everything the table above lists. These aren't build artifacts you can regenerate from source at will and forget — they're the actual configuration Copilot, VS Code, and Claude Code read at runtime, and other contributors (and CI) need them present in the repo. Treat `LEARNINGS.md` as living project documentation, not disposable output — never delete it to "clean up" a re-sync.

**In this canonical starter-kit repo itself**, nothing is generated: aigov refuses to write into the kit. To try a change, install into a scratch folder: `python tooling/aigov.py install --output /tmp/aigov-check --targets copilot claude-code --templates`.
