# Mistakes & Learnings Log Protocol

> **Applies To:** All AI Assistants, Inline Copilots, and Agentic Workflows
> **Enforcement Level:** Mandatory

---

## 📓 1. Purpose

AI assistants must not make the same mistake twice, and must not require the same correction more than once. This protocol turns corrections, mistakes, and non-obvious gotchas into a durable, per-repository memory instead of losing them at the end of a session.

---

## ✍️ 2. When to Log an Entry

Log an entry to `LEARNINGS.md` at the root of the working repository whenever any of the following occurs during a session:

* **You were corrected.** The user pointed out that your output, approach, or assumption was wrong.
* **You hit a non-obvious gotcha.** A build quirk, hidden dependency, misleading error message, environment constraint, or "obvious in hindsight" trap that cost real time to diagnose.
* **You discover an undocumented pattern or convention.** Something a newcomer (human or AI) would not guess from reading the code alone, but that the codebase or team actually relies on.
* **A repeated or recurring class of mistake.** Even if this is the first time *you* made it, if it's the kind of mistake that's easy to make again, log it pre-emptively.

Do **not** log routine debugging, one-off typos, or anything already covered by an existing entry — update the existing entry instead of duplicating it.

---

## 📖 3. Before Starting Work

* At the start of a new task, read `LEARNINGS.md` in full before writing code or making changes.
* If an existing entry is relevant to the current task, follow its guidance explicitly and do not reintroduce the same mistake.
* If `LEARNINGS.md` does not exist yet in the repository, create it using the format below the first time you have an entry to record.

---

## 🧾 4. Entry Format

Append new entries to `LEARNINGS.md` using this structure, newest entry last:

```markdown
## YYYY-MM-DD — Short descriptive title

**Context:** What task or area this came up in.

**Mistake / Gotcha:** What went wrong, or what was non-obvious.

**Correct Pattern:** What to do instead, going forward.
```

Keep entries short and actionable — this file is a checklist for future sessions, not a narrative changelog. Prefer one entry per distinct lesson over one large entry covering several unrelated issues.

---

## 🚀 Deployment Behavior

The governance kit creates `LEARNINGS.md` at the repository root once, **only if it does not already exist**, and never overwrites or deletes it. Accumulated learnings survive every update.

## 🧠 Claude Code: Prefer the Skill

On Claude Code, `global/skills/learnings-log/` enforces this same protocol as a self-triggering Skill — it fires at the start of every task and immediately after a correction, rather than depending on this instructions file being remembered inside a large concatenated `AGENTS.md`. This instructions file remains the enforcement mechanism for Copilot/VS Code, which have no Skills system to self-trigger from.
