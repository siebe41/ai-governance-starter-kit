# Where aigov puts things, and why

This is the complete list of files `tooling/aigov.py` writes into a project repo. If a path isn't in this table, aigov doesn't write it.

## The rules

1. **You choose the AI tools ("targets").** `install` asks, or you pass `--targets`. The answer is saved in `.ai-governance.json`. aigov never picks a tool for you. With no targets set, `sync` refuses to run.
2. **Each item goes to the one path its tool documents** (linked in the tables below). Nothing is written for a tool you didn't choose, and nothing goes to a path no tool reads.
3. **If two chosen tools read the same path, aigov writes it once there.** Today that only applies to skills: Copilot also reads `.claude/skills/`, so a repo using both tools gets one copy there.
4. **Every file aigov writes is recorded** in `.ai-governance.json` (`generated`), along with a fingerprint of its contents. That record is how `sync` removes files you've excluded and how `migrate` knows what it's allowed to delete. aigov never modifies or deletes a file it didn't write, and it stops rather than overwrite a file someone edited by hand.

## GitHub Copilot (`copilot`)

Everything goes under `.github/` except the VS Code MCP file.

| Kit source | Written to | Read by | Docs |
| --- | --- | --- | --- |
| `global/instructions/*.md` + project `local_dirs` | `.github/copilot-instructions.md` (one file, always loaded) | Copilot in VS Code, Visual Studio, github.com, CLI | [Custom instructions](https://code.visualstudio.com/docs/agent-customization/custom-instructions) |
| `templates/<Domain>/instructions/*.md` | `.github/instructions/<domain>-<name>.instructions.md`, scoped with `applyTo` from `templates/<Domain>/overlay.json` | Same, but only for matching files | [Custom instructions](https://code.visualstudio.com/docs/agent-customization/custom-instructions) |
| `global/prompts/*.md` | `.github/prompts/<name>.prompt.md` | Copilot Chat prompt picker (`/name`) | [Prompt files](https://code.visualstudio.com/docs/agent-customization/prompt-files) |
| `global/agents/*.yml`, `*.agent.md` | `.github/agents/<name>.agent.md` | Copilot agent picker | [Custom agents](https://code.visualstudio.com/docs/agent-customization/custom-agents) |
| `global/skills/<name>/` | `.github/skills/<name>/` | Copilot agent skills | [Agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills) |
| `global/mcp/mcp-servers.json` | `.vscode/mcp.json` (`servers` key) | Copilot in VS Code | [MCP servers in VS Code](https://code.visualstudio.com/docs/copilot/customization/mcp-servers) |

**Not a file:** Copilot's cloud agent on github.com reads MCP servers from the repo's **Settings > Copilot > MCP servers** page, not from the repo ([docs](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/configure-mcp-servers)). aigov reminds you of this after every run; it can't set it for you.

## Claude Code (`claude-code`)

| Kit source | Written to | Docs |
| --- | --- | --- |
| `global/instructions/*.md` + domain overlays + project `local_dirs` | `CLAUDE.md` (one file, always loaded) | [Memory](https://code.claude.com/docs/en/memory) |
| `global/prompts/*.md` | `.claude/commands/<name>.md` (slash commands) | [Skills and commands](https://code.claude.com/docs/en/slash-commands) |
| `global/agents/*.yml`, `*.agent.md` | `.claude/agents/<name>.md` | [Subagents](https://code.claude.com/docs/en/sub-agents) |
| `global/skills/<name>/` | `.claude/skills/<name>/` | [Skills](https://code.claude.com/docs/en/slash-commands) |
| `global/mcp/mcp-servers.json` | `.mcp.json` (`mcpServers` key) | [MCP](https://code.claude.com/docs/en/mcp) |

Domain overlays are added to `CLAUDE.md`, so they load on every Claude Code request. Claude Code documents path-specific rules too; scoping overlays with them is a possible future change.

Claude Code now documents custom commands as part of skills; files in `.claude/commands/` keep working and create the same `/name` commands.

## Both tools

Each tool gets its own files from the tables above, except skills, which are written once to `.claude/skills/`.

## Always, for every target

| File | Behavior |
| --- | --- |
| `.ai-governance.json` | Your choices (`targets`, `templates`, `exclude`, `local_dirs`) and the record of generated files. Commit it. |
| `LEARNINGS.md` | Seeded once from `global/LEARNINGS.template.md`. aigov never tracks, overwrites, or deletes it; it holds your project's own learnings. |

## Things aigov copies as written

**MCP environment variables.** aigov copies `global/mcp/mcp-servers.json` values exactly as written. VS Code and Claude Code use different syntax for environment variables in MCP config, so check each tool's docs and write the placeholders in the form your tools expect.

## Changing this table

A path change is a breaking change: bump the major version in `VERSION`, add a `CHANGELOG.md` entry, and update this file in the same pull request. Existing repos move with `aigov.py migrate`.
