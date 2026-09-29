# Contributing to the AI Governance Starter Kit

This repository is the canonical source of truth for your org's AI tooling rules. A change here rolls out to every project that syncs against it — review changes with that blast radius in mind.

---

## Change Categories & Review Bar

| Path | What it controls | Review bar |
| :--- | :--- | :--- |
| `global/instructions/` | Non-negotiable guardrails (security, coding, testing, the learnings-log protocol) | Governance sign-off (security/platform lead) — these are mandatory for every synced project. |
| `global/mcp/mcp-servers.json` | Approved MCP servers | Governance sign-off — this is the org's "approved tools" allowlist. |
| `global/agents/`, `global/prompts/`, `global/skills/` | Opt-in agent roles, prompt templates, and Claude Skills | Standard code review — these are selectable/excludable per project, not mandatory. |
| `templates/<Domain>/` | Domain-specific overlays (Cloud, UI, DevOps, ...) | Owned by the relevant domain team; standard code review. |
| `tooling/` | The deployment engine itself | Standard code review **plus** a local dry-run before merging — every downstream project depends on this working correctly. |

---

## Before Opening a PR

1. **Any change under `global/` or `templates/`, or to `tooling/aigov.py`:** install into a scratch folder for every target and confirm the change lands where [`TARGETS.md`](/TARGETS.md) says it should, with no errors:
   ```bash
   python tooling/aigov.py install --output /tmp/aigov-check --targets copilot claude-code --templates
   ```
2. **Bump the version.** Update `VERSION` and add an entry to `CHANGELOG.md` for any change under `global/`, `templates/`, or `tooling/aigov.py`. Patch for wording/doc fixes, minor for additive instructions/agents/prompts/templates, major for anything that changes an existing file path, output format, or breaks a downstream project's assumptions.
3. **New agent role:** add it to `global/agents/readme.md`'s role list *and* its "How to Use" section — an agent with no usage docs isn't done.
4. **New prompt template:** add it to `global/prompts/readme.md` the same way.
5. **New skill:** add it to `global/skills/readme.md` the same way — see that file's "Adding Your Own Skill" section for the `SKILL.md` frontmatter contract.
6. **New domain template:** add a `templates/<Domain>/readme.md` describing what it overlays and why, so it's self-explanatory to whoever selects it. If its rules only apply to some files, add `templates/<Domain>/overlay.json` with an `applyTo` glob so Copilot loads them only for those files.
7. **Changes to `global/instructions/`:** double-check the wording still reads as a rule an AI assistant will actually follow — imperative, unambiguous, testable — not a description of a rule.

If a change should be optional per-project rather than universal, it belongs under `global/` where it can be excluded via `.ai-governance.json` (see the main `README.md`) — it does not need its own domain template just to be skippable.

---

## Governance Ownership

Once you fork this repo for your org, enforce the review bar above with a `CODEOWNERS` file, e.g.:

```
/global/instructions/    @your-org/platform-security
/global/mcp/             @your-org/platform-security
/templates/Cloud/        @your-org/cloud-team
/templates/UI/           @your-org/frontend-team
/templates/DevOps/       @your-org/devops-team
```

This repo doesn't ship a `CODEOWNERS` file itself, since ownership is org-specific — add one to your fork as part of onboarding (see `QUICKSTART.md`).

---

## Reporting Issues

Open an issue or discussion thread describing the gap or proposed change before submitting a large PR, especially for anything touching `global/instructions/` — it affects every project synced against this repo.
