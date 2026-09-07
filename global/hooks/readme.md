# 🪝 Claude Code Hooks

This folder contains canonical [Claude Code hook](https://docs.claude.com/en/docs/claude-code/hooks) fragments — small JSON files, one per hook, that `tooling/sync_configs.py` merges into a target repo's `.claude/settings.json`.

A hook is how a governance rule stops being "the model has to remember this" and becomes "the harness enforces this outside model context." `global/instructions/` documents a policy in prose that a model reads and (usually) follows; a hook is the same policy encoded as a script that runs whether or not the model remembers it exists. Reach for a hook whenever an instruction is phrased as "always run X before/after Y" — that is a hook, not a reminder.

---

## 📄 Included Hooks

* **`lint-before-finish.json`**: `Stop` hook. If the working tree has any uncommitted change when Claude tries to finish, runs `npm run lint`; on failure, blocks finishing and feeds the lint output back so it gets fixed before the turn ends. Silent no-op on a clean tree, so it costs nothing on a read-only or already-finished turn. Assumes an npm `lint` script and `jq` on PATH — see the fragment's own `description` field for how to adapt it to a non-npm stack.

---

## 🔒 A Hook Runs Arbitrary Shell — Review Before Adding One

This is the one category in `global/` whose assets execute on the deploying machine rather than just being read by a model, so `global/instructions/00-security-governance.md`'s "No Untrusted Dependencies" rule applies with extra force here: never vendor a hook whose command you have not read in full, and never write one that pipes remote content into a shell. Keep commands narrowly scoped to what the hook's stated purpose needs (a lint runner has no reason to touch the network or read credentials), and prefer failing open (silent no-op) over failing in a way that could mask a real error, unless the whole point of the hook is to block on that error.

---

## 🚀 Deployment Behavior

Unlike `skills/` (a fresh directory copy per skill) or `mcp/` (one file, transformed and rewritten wholesale), `.claude/settings.json` is a single file that a target repo may already have hand-edited content in — permissions, env vars, other hooks. So deployment here is a **merge, not an overwrite**:

1. `tooling/sync_configs.py` reads every `*.json` fragment in `global/hooks/` (plus any selected template's `hooks/` and any `local_dirs` override).
2. Each fragment names one `event` (`Stop`, `PostToolUse`, etc.) and one `hook` object — the exact shape Claude Code expects inside `settings.json`'s `hooks.<event>` array.
3. That object is appended to the target's `.claude/settings.json` → `hooks.<event>` array, **unless an identical entry is already there** — re-running the sync is a no-op for hooks you already have, and anything else already in the file (a hand-written hook, `permissions`, etc.) is left untouched.
4. A `.claude/settings.json` that fails to parse as JSON is left alone with a warning rather than risk corrupting a hand-edited file — fix it and re-run.

`readme.md` is not a fragment, so it's naturally skipped (only `*.json` files are read).

---

## ➕ Adding Your Own Hook

1. Create `global/hooks/<your-hook-name>.json`:
   ```json
   {
     "name": "your-hook-name",
     "description": "One or two sentences: what triggers it, what it does, what it assumes about the target repo (a script on PATH, a package.json field, etc.).",
     "event": "PostToolUse",
     "hook": {
       "matcher": "Write|Edit",
       "hooks": [
         { "type": "command", "command": "…", "timeout": 60 }
       ]
     }
   }
   ```
   `event` and the inner `hook` object are exactly what ends up under `.claude/settings.json`'s `hooks.<event>` array — copy the shape from the [hooks reference](https://docs.claude.com/en/docs/claude-code/hooks) or an existing fragment here rather than guessing at it.
2. Prove the command actually does what you claim before committing it — pipe a synthesized hook-input payload into it by hand (see the fragment's own `description` for the assumptions it makes) rather than trusting that it will work once deployed.
3. Add it to the **Included Hooks** list above.
4. If you don't want it maintained centrally, you don't need to touch this folder — see the top-level `README.md`'s "Include/Exclude & Bring Your Own" section for adding project-specific hooks without editing the vendored kit.
