---
name: finishing-a-development-branch
description: Use when implementation is complete and all tests pass, to decide how to integrate the work — merge, push a PR, or leave it as-is. Never guesses the answer; always presents the choice and waits.
---

# Finishing a Development Branch

## Core Principle

Verify tests → detect environment → present options → execute the chosen option → clean up. The integration decision belongs to the human, not to you — present the menu and wait for an answer instead of assuming what they want.

## Step 1: Verify Tests

Run the full test suite. If anything fails, report the failures and stop here — the options menu only comes after a green suite.

## Step 2: Detect the Environment

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
WORKTREE_PATH=$(git rev-parse --show-toplevel)   # capture now — cleanup runs after a `cd`
```

* `GIT_DIR == GIT_COMMON` (normal repo), or a named-branch worktree → standard 3-option menu.
* Detached HEAD (externally-managed workspace) → reduced 2-option menu (no local merge — there's no branch to merge from).

## Step 3: Confirm the Base Branch

Don't assume `main`/`master`. If it isn't already stated in the plan or conversation, ask: *"This branch split from `<your best guess>` — is that correct?"* Merging into the wrong base is expensive to undo.

## Step 4: Present Options — Verbatim, Then Wait

**Normal repo / named branch:**
```
Implementation complete. What would you like to do?
1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
```

**Detached HEAD:**
```
Implementation complete. You're on a detached HEAD.
1. Push as a new branch and create a Pull Request
2. Keep as-is (I'll handle it later)
```

Discarding the work is **not** on this menu — it happens only if the human explicitly asks for it afterward (see below).

## Step 5: Execute the Choice

**Merge locally:** `cd` to the main repo root, `git checkout <base-branch> && git pull && git merge <feature-branch>`, then re-run the full test suite on the merged result. Tests fail on the merge → stop, leave the worktree/branch in place, investigate — nothing has been pushed, so this is fully recoverable. Tests pass → clean up the worktree (Step 6), then `git branch -d <feature-branch>`.

**Push + PR:** `git push -u origin <feature-branch>` (from detached HEAD, name it explicitly: `git push origin HEAD:refs/heads/<new-branch>`), then open the PR against `<base-branch>` following the repo's template if one exists, and report the URL. Keep the worktree — PR feedback gets addressed there.

**Keep as-is:** report the branch name and worktree path; do nothing else.

**Discard (only if explicitly requested afterward):** confirm before acting — list the branch, every commit that would be lost, and the worktree path — and require the literal typed word `discard` before running `git branch -D <feature-branch>` and removing the worktree. "Yeah, get rid of it" is not confirmation; wait for the exact word.

## Step 6: Clean Up the Worktree

Runs only for a completed local merge or a confirmed discard — Push+PR and Keep-as-is always preserve the worktree.

* `GIT_DIR == GIT_COMMON` → no worktree exists, nothing to clean up.
* Worktree lives under `.worktrees/` or `worktrees/` → this tooling owns it: `git worktree remove "$WORKTREE_PATH" && git worktree prune`.
* Removal refused (`contains modified or untracked files`) → **never** pass `--force` on your own initiative. Those files exist nowhere else. Show the human `git -C "$WORKTREE_PATH" status --porcelain -uall` and ask whether to commit them, move them out, or delete them — then act on their answer.
* Worktree lives elsewhere → it's not yours to clean up; leave it alone.

## Common Rationalizations — and Why They're Wrong

| Excuse | Reality |
| :--- | :--- |
| "Tests passed earlier this session" | Run the suite on the tree you're about to integrate — a green run only proves the tree it ran on. |
| "They obviously want it merged" | Integration is the human's call. Present the menu and wait. |
| "'Yeah, get rid of it' counts as confirmation" | Only the literal typed word `discard` authorizes deletion. |
| "The base branch is obviously main" | Confirm it. Merging into the wrong base is expensive to undo. |
| "Removal was refused — `--force` just finishes the cleanup" | Refusal means files exist only in that worktree. Show the human and ask, don't force. |

---
Adapted from [obra/superpowers](https://github.com/obra/superpowers/tree/main/skills/finishing-a-development-branch) (MIT License, © Jesse Vincent).
