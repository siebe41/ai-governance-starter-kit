# Quickstart

Two paths, depending on who you are. Both take a few minutes.

---

## Technical Lead: onboard one project

1. **Bring the kit into your project** (pick one — see the main `README.md` for the tradeoffs):
   ```bash
   git subtree add --prefix vendor/ai-governance https://github.com/YOUR_ORG/ai-governance-starter-kit.git main --squash
   ```
2. **Run the sync** from your project root:
   ```bash
   python vendor/ai-governance/tooling/sync_configs.py --output .
   ```
3. **Pick domain overlay(s)** when prompted (Cloud / UI / DevOps / ...), or press Enter for Global rules only.
4. **Commit the generated files** — see "What to Commit" below.
5. Open your editor / Copilot Chat / Claude Code. The guardrails, prompts, agents, and skills are live — nothing else to configure.

Re-run step 2 any time `vendor/ai-governance` is updated to pick up the latest org rules. It's safe to re-run: your selection is remembered in `.ai-governance.json`, `LEARNINGS.md` is never overwritten, everything else is regenerated in place.

**Don't want everything?** Open `.ai-governance.json` (written after your first sync) and add filenames to `exclude` per category — e.g. `"prompts": ["caveman-mode.md"]` — then re-run the sync with no flags; it reuses the file. Want to add something of your own without editing the vendored kit? Drop it in a project-local folder (e.g. `governance-local/skills/my-skill/SKILL.md`) and list that folder under `local_dirs` in the same file. Full details in the main `README.md`'s "Include/Exclude & Bring Your Own" section.

---

## IT Admin: roll this out org-wide

1. Fork this repo to your org's Git server.
2. Edit `global/instructions/`, `global/prompts/`, `global/agents/`, and `global/mcp/mcp-servers.json` to match your org's actual policies — the shipped content is a working example, not a finished policy.
3. Add a `CODEOWNERS` file to enforce the review bar described in `CONTRIBUTING.md` (governance sign-off required for `global/instructions/` and `global/mcp/`).
4. Populate `templates/<Domain>/` for any domain overlays your org needs (Cloud, UI, DevOps, ...) — the kit ships the pattern, not populated content, since it's org- and stack-specific.
5. Bump `VERSION` and add a `CHANGELOG.md` entry for every change, so project teams can tell whether they're on the latest rules — every generated `copilot-instructions.md` / `CLAUDE.md` is stamped with the version it came from.
6. Point every project at your fork (see "Pre-Onboarding Setup: Fork vs. Subtree" in the main `README.md`) and make `python tooling/sync_configs.py` part of new-project onboarding.

---

## What Gets Generated

| File | Purpose | Behavior on re-sync |
| :--- | :--- | :--- |
| `.github/copilot-instructions.md` | Copilot Workspace instructions | Always regenerated |
| `CLAUDE.md` | Claude Code / Claude Agent SDK instructions | Always regenerated |
| `.vscode/prompts/*.md` | Selectable prompt templates | Always regenerated |
| `.copilot/agents/*.yml` | Custom agent role definitions | Always regenerated |
| `.claude/skills/<name>/` | Claude Code Skills | Always regenerated |
| `.vscode/mcp.json`, `.copilot/mcp.json` | MCP server registry | Always regenerated |
| `LEARNINGS.md` | Per-repo mistakes/gotchas log | Seeded once — **never** overwritten |
| `.ai-governance.json` | Your template/exclude/local-dirs selection | Written after every sync; hand-edit it any time — the next sync reads your edits back |

---

## What to Commit

**In your project** (the sync target): commit everything the table above lists. These aren't build artifacts you can regenerate from source at will and forget — they're the actual configuration Copilot, VS Code, and Claude Code read at runtime, and other contributors (and CI) need them present in the repo. Treat `LEARNINGS.md` as living project documentation, not disposable output — never delete it to "clean up" a re-sync.

**In this canonical starter-kit repo itself**, the opposite applies: `.github/copilot-instructions.md`, `CLAUDE.md`, `.vscode/`, `.copilot/`, `.claude/skills/`, `.ai-governance.json`, and `LEARNINGS.md` are deployment *outputs*, not source. Running `sync_configs.py` with no `--output` flag writes into the repo root by default — the shipped root `.gitignore` keeps those paths from accidentally landing in the canonical source if you run it locally. If you're editing this kit itself, use `--output /tmp/sync-check` (or similar) to dry-run without touching your working tree.
