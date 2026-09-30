# 🪝 Claude Code Hooks

This folder contains canonical [Claude Code hook](https://docs.claude.com/en/docs/claude-code/hooks) fragments — small JSON files, one per hook, that `tooling/aigov.py` combines into a target repo's `.claude/settings.json` (a Claude Code feature; Copilot ignores the file).

A hook is how a governance rule stops being "the model has to remember this" and becomes "the harness enforces this outside model context." `global/instructions/` documents a policy in prose that a model reads and (usually) follows; a hook is the same policy encoded as a script that runs whether or not the model remembers it exists. Reach for a hook whenever an instruction is phrased as "always run X before/after Y" — that is a hook, not a reminder.

---

## 📄 Included Hooks

* **`lint-before-finish.json`**: `Stop` hook. If the working tree has any uncommitted change when Claude tries to finish, runs `npm run lint`; on failure, blocks finishing and feeds the lint output back so it gets fixed before the turn ends. Silent no-op on a clean tree, so it costs nothing on a read-only or already-finished turn. Assumes an npm `lint` script and `jq` on PATH — see the fragment's own `description` field for how to adapt it to a non-npm stack.

---

## 🔒 A Hook Runs Arbitrary Shell — Review Before Adding One

This is the one category in `global/` whose assets execute on the deploying machine rather than just being read by a model, so `global/instructions/00-security-governance.md`'s "No Untrusted Dependencies" rule applies with extra force here: never vendor a hook whose command you have not read in full, and never write one that pipes remote content into a shell. Keep commands narrowly scoped to what the hook's stated purpose needs (a lint runner has no reason to touch the network or read credentials), and prefer failing open (silent no-op) over failing in a way that could mask a real error, unless the whole point of the hook is to block on that error.

---

## 🚀 Deployment Behavior

All fragments become **one generated file**, `.claude/settings.json`, which aigov owns and records like every other file it writes:

1. `tooling/aigov.py` reads every `*.json` fragment in `global/hooks/` (plus any selected template's `hooks/` and any `local_dirs` override), skipping any named in `exclude.hooks` (by stem, e.g. `lint-before-finish`).
2. Each fragment names one `event` (`Stop`, `PostToolUse`, etc.) and one `hook` object — the exact shape Claude Code expects inside `settings.json`'s `hooks.<event>` array. An identical entry from two layers is written once. A malformed fragment stops the run rather than being skipped.
3. The result is written as `{"hooks": {...}}`. It is only written when at least one hook is selected; excluding them all removes the file on the next `sync`.
4. **aigov never merges into a hand-written `.claude/settings.json`.** If the repo already has one, the run stops (as it would for any file aigov didn't write). Either move shared settings aside, or exclude the hooks and manage `settings.json` yourself. Personal settings belong in `.claude/settings.local.json`, which aigov never touches.

`readme.md` is not a fragment, so it's naturally skipped (only `*.json` files are read). v1.6 repos whose `settings.json` holds exactly the kit's hooks are recognized by `aigov.py migrate`; anything else in that file makes migrate stop and ask you to move it first.

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
