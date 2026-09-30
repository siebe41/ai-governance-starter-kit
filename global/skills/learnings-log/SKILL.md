---
name: learnings-log
description: Use at the start of every task — read LEARNINGS.md before writing any code — and again immediately after being corrected by the user or hitting a non-obvious gotcha, to append an entry. Self-triggers so the mistakes/learnings protocol doesn't depend on the assistant remembering to check a passive instructions file.
---

# Learnings Log

Enforces `global/instructions/03-learnings-log.md` as an active behavior instead of a passive rule: an AI assistant must not make the same mistake twice, and must not require the same correction more than once.

## Trigger 1: Start of Every Task

Before writing code or making changes, read `LEARNINGS.md` at the repository root in full.

- If it doesn't exist yet, there's nothing to read — proceed, and create it the first time you have an entry to record (Trigger 2).
- If an entry is relevant to the current task, follow its guidance explicitly. Don't reintroduce a mistake that's already logged.

## Trigger 2: Immediately After a Correction or Gotcha

Append an entry the moment any of these happens — don't wait until the end of the session, and don't rely on remembering to do it later:

- **You were corrected.** The user pointed out your output, approach, or assumption was wrong.
- **You hit a non-obvious gotcha.** A build quirk, hidden dependency, misleading error message, environment constraint, or "obvious in hindsight" trap that cost real time.
- **You found an undocumented pattern or convention** the codebase relies on that a newcomer wouldn't guess from reading the code alone.
- **You made a mistake that's easy to repeat**, even if this is the first time — log it pre-emptively.

Don't log routine debugging, one-off typos, or anything an existing entry already covers — update that entry instead of duplicating it.

## Entry Format

Append to `LEARNINGS.md`, newest entry last:

```markdown
## YYYY-MM-DD — Short descriptive title

**Context:** What task or area this came up in.

**Mistake / Gotcha:** What went wrong, or what was non-obvious.

**Correct Pattern:** What to do instead, going forward.
```

Keep entries short and actionable — this file is a pre-flight checklist for future sessions, not a narrative changelog. One entry per distinct lesson, not one entry covering several unrelated issues.

## Boundaries

This skill only reads and appends to `LEARNINGS.md`. It doesn't create the file proactively (that happens on first install via `tooling/aigov.py`, or on first entry if syncing hasn't happened yet), and it never rewrites or deletes an existing entry except to update it when the same lesson recurs.

---
See `global/instructions/03-learnings-log.md` for the full protocol and `global/LEARNINGS.template.md` for how the file gets seeded into a project. This skill is the Claude-Code-native, self-triggering enforcement of that same protocol — Copilot/VS Code, which have no Skills system to self-trigger from, rely on the instructions file being present in `AGENTS.md` instead.
