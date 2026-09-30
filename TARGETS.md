# Where aigov puts things, and why

This is the complete list of files `tooling/aigov.py` writes into a project repo. If a path isn't in this table, aigov doesn't write it.

## The rules

1. **There's no tool to choose.** Every repo gets the files for both GitHub Copilot and Claude Code. The always-on rules go to one `AGENTS.md`, which both tools read, so there's nothing to keep in step between two instruction files. A repo that uses only one tool just has a few files the other tool reads; use `exclude` in `.ai-governance.json` to leave out anything you don't want (for example the factory workflows).
2. **Each item goes to the one path its tool documents** (linked in the tables below). Nothing goes to a path no tool reads.
3. **If both tools read the same path, aigov writes it once there.** That's `AGENTS.md` and skills (Copilot also reads `.claude/skills/`).
4. **Every file aigov writes is recorded** in `.ai-governance.json` (`generated`), along with a fingerprint of its contents. That record is how `sync` removes files you've excluded and how `migrate` knows what it's allowed to delete. aigov never modifies or deletes a file it didn't write, and it stops rather than overwrite a file someone edited by hand.

## Both tools (`shared`)

| Kit source | Written to | Read by | Docs |
| --- | --- | --- | --- |
| `global/instructions/*.md` + project `local_dirs` | `AGENTS.md` (one file, always loaded) | Copilot (VS Code, cloud agent, CLI) and Claude Code v2.1.277+ | [Copilot custom instructions](https://code.visualstudio.com/docs/agent-customization/custom-instructions), [Claude Code AGENTS.md](https://code.claude.com/docs/en/memory#agents-md) |
| `global/skills/<name>/` | `.claude/skills/<name>/` | Copilot agent skills and Claude Code skills | [Copilot agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills), [Claude Code skills](https://code.claude.com/docs/en/slash-commands) |

**A `CLAUDE.md` hides `AGENTS.md` from Claude Code.** By default Claude Code reads `AGENTS.md` only when there's no `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` in the working directory or above it. aigov doesn't write any of those, and it warns after a run if one exists. To keep yours, put `@AGENTS.md` on its first line ([docs](https://code.claude.com/docs/en/memory#share-one-file-with-other-coding-tools)). Do the same on Claude Code older than v2.1.277, which reads only `CLAUDE.md`.

**Domain overlays stay out of `AGENTS.md`.** `AGENTS.md` can't be scoped to file types, and overlays (like the ~700-line UI accessibility rules) should load only for matching files. So each tool gets them in its own path-scoped format, both using the glob in `templates/<Domain>/overlay.json`.

## GitHub Copilot (`copilot`)

Everything goes under `.github/` except the VS Code MCP file.

| Kit source | Written to | Read by | Docs |
| --- | --- | --- | --- |
| `templates/<Domain>/instructions/*.md` | `.github/instructions/<domain>-<name>.instructions.md`, scoped with `applyTo` from `templates/<Domain>/overlay.json` | Copilot in VS Code, Visual Studio, github.com, CLI, only for matching files | [Custom instructions](https://code.visualstudio.com/docs/agent-customization/custom-instructions) |
| `global/prompts/*.md` | `.github/prompts/<name>.prompt.md` | Copilot Chat prompt picker (`/name`) | [Prompt files](https://code.visualstudio.com/docs/agent-customization/prompt-files) |
| `global/agents/*.yml`, `*.agent.md` | `.github/agents/<name>.agent.md` | Copilot agent picker | [Custom agents](https://code.visualstudio.com/docs/agent-customization/custom-agents) |
| `global/mcp/mcp-servers.json` | `.vscode/mcp.json` (`servers` key) | Copilot in VS Code | [MCP servers in VS Code](https://code.visualstudio.com/docs/copilot/customization/mcp-servers) |

**Not a file:** Copilot's cloud agent on github.com reads MCP servers from the repo's **Settings > Copilot > MCP servers** page, not from the repo ([docs](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/configure-mcp-servers)). aigov reminds you of this after every run; it can't set it for you.

## Claude Code (`claude-code`)

| Kit source | Written to | Docs |
| --- | --- | --- |
| `templates/<Domain>/instructions/*.md` | `.claude/rules/<domain>-<name>.md`, scoped with `paths` from `templates/<Domain>/overlay.json` (loaded for every file if there's no glob) | [Path-specific rules](https://code.claude.com/docs/en/memory#path-specific-rules) |
| `global/prompts/*.md` | `.claude/commands/<name>.md` (slash commands) | [Skills and commands](https://code.claude.com/docs/en/slash-commands) |
| `global/agents/*.yml`, `*.agent.md` | `.claude/agents/<name>.md` | [Subagents](https://code.claude.com/docs/en/sub-agents) |
| `global/mcp/mcp-servers.json` | `.mcp.json` (`mcpServers` key) | [MCP](https://code.claude.com/docs/en/mcp) |
| `global/hooks/*.json` | `.claude/settings.json` (`hooks` key). aigov owns the whole file; it won't merge into a hand-written one. | [Hooks](https://code.claude.com/docs/en/hooks) |
| `global/workflows/*.yml` | `.github/workflows/<name>.yml`, by name only; the repo's other workflows are never touched | [GitHub Actions](https://docs.github.com/en/actions) |
| `global/factory/` | `.factory/`, only when a `factory-*` workflow is written (the workflows reference that path literally) | [`docs/factory-playbook.md`](/docs/factory-playbook.md) |

Hooks are a Claude Code feature, and the shipped workflows run Claude Code and follow the factory skills. The workflows ship inert (`enabled: false`) and do nothing until a repo turns them on in its own `.factory.json`. To leave them out, add them to `exclude.workflows`; excluding every `factory-*` workflow also drops `.factory/`.

Claude Code now documents custom commands as part of skills; files in `.claude/commands/` keep working and create the same `/name` commands.

## Always

| File | Behavior |
| --- | --- |
| `.ai-governance.json` | Your choices (`templates`, `exclude`, `local_dirs`) and the record of generated files. Commit it. |
| `LEARNINGS.md` | Seeded once from `global/LEARNINGS.template.md`. aigov never tracks, overwrites, or deletes it; it holds your project's own learnings. |

## Things aigov copies as written

**MCP environment variables.** aigov copies `global/mcp/mcp-servers.json` values exactly as written. VS Code and Claude Code use different syntax for environment variables in MCP config, so check each tool's docs and write the placeholders in the form your tools expect.

## Changing this table

A path change is a breaking change: bump the major version in `VERSION`, add a `CHANGELOG.md` entry, and update this file in the same pull request. Existing repos move with `aigov.py migrate`.
