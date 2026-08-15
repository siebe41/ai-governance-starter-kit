---
name: using-git-worktrees
description: Use before starting feature work that needs isolation from the current workspace, or before executing a multi-step implementation plan — ensures an isolated workspace exists via a native tool or a git worktree fallback.
---

# Using Git Worktrees

## Core Principle

Detect existing isolation first. Then prefer a native tool. Fall back to a manual git worktree only if no native tool is available. Never fight the harness you're running in.

## Step 0: Check Whether You're Already Isolated

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
```

If `GIT_DIR != GIT_COMMON`, you're already in a linked worktree — **but** this is also true inside a git submodule, so check that first:

```bash
git rev-parse --show-superproject-working-tree 2>/dev/null
# If this prints a path, you're in a submodule, not a worktree — treat as a normal repo.
```

Already isolated (and not a submodule)? Skip straight to Step 2 — do not create another worktree on top of one.

## Step 1: Create Isolation, If You Need It

If the user hasn't already told you their worktree preference, ask before creating one: *"Would you like me to set up an isolated worktree? It protects your current branch from changes."* Honor a declared preference without re-asking; if they decline, work in place and skip to Step 2.

**1a. Native tool first.** If your environment provides a worktree/workspace tool (e.g. an `EnterWorktree`-style tool, a `/worktree` command, a `--worktree` flag), use it and skip to Step 2. It owns directory placement, branching, and cleanup — running `git worktree add` on top of it creates state the harness can't see or manage.

**1b. Manual git worktree, only if 1a doesn't apply:**
1. Directory: honor an explicit user preference first; otherwise reuse an existing `.worktrees/` or `worktrees/` (in that order) if one exists; otherwise default to `.worktrees/` at the project root.
2. **Verify it's gitignored before creating anything:** `git check-ignore -q .worktrees || git check-ignore -q worktrees`. If not ignored, add it to `.gitignore` and commit that change first — an unignored worktree directory will get its entire contents committed into the repo.
3. Create it: `git worktree add "<path>" -b "<branch-name>" && cd "<path>"`.
4. If `git worktree add` fails on a permission/sandbox error, tell the user isolation was blocked and continue in the current directory instead.

## Step 2: Project Setup

Auto-detect and install: `npm install` (package.json), `cargo build` (Cargo.toml), `pip install -r requirements.txt` / `poetry install` (Python), `go mod download` (go.mod).

## Step 3: Verify a Clean Baseline

Run the project's test command before touching anything. Tests fail here → report and ask whether to proceed or investigate first; a dirty baseline makes every later failure ambiguous. Tests pass → report ready and start the actual work.

## Quick Reference

| Situation | Action |
| :--- | :--- |
| Already in a linked worktree | Skip creation, go to Step 2 |
| In a submodule | Treat as a normal repo |
| Native worktree tool available | Use it, skip the manual fallback |
| `.worktrees/` or `worktrees/` exists | Reuse it (verify it's gitignored first) |
| Directory not gitignored | Add to `.gitignore` and commit before creating the worktree |
| `git worktree add` hits a permission error | Work in place, tell the user why |
| Baseline tests fail | Report and ask before proceeding |

---
Adapted from [obra/superpowers](https://github.com/obra/superpowers/blob/main/skills/using-git-worktrees/SKILL.md) (MIT License, © Jesse Vincent).
