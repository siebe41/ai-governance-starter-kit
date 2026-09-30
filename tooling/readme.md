# 🛠️ Deployment Tooling

## `aigov.py`

Writes this kit's assets into a project repo: one `AGENTS.md` that GitHub Copilot and Claude Code both read, plus each tool's own files. There's no tool to choose. Python 3.9+, standard library only.

```bash
python tooling/aigov.py install   --output path/to/project   # asks: which overlays?
python tooling/aigov.py sync      --output path/to/project   # re-apply the kit; never asks
python tooling/aigov.py sync --check                        # CI: fail if out of date or hand-edited
python tooling/aigov.py migrate   --output path/to/project   # move a v1 or v2 repo to AGENTS.md
python tooling/aigov.py status    --output path/to/project   # what's installed, per file
```

`--output` defaults to the current folder. For scripts and CI, pass answers as flags: `--templates UI` (or `--templates` alone for none), and `--yes` for `migrate`. The v2 `--targets` flag is accepted and ignored.

Where each item lands, and why, is in [`TARGETS.md`](/TARGETS.md). What aigov refuses to do is in the main `README.md` under "What aigov refuses to do".

## How it works

1. **Plan.** Build the full list of files to write from `global/`, the selected `templates/`, and the project's `local_dirs`, for both tools.
2. **Check.** Compare the plan against the project and the record in `.ai-governance.json`. Any file that exists but wasn't written by aigov, or was written by aigov and then edited, stops the run before anything changes.
3. **Apply.** Write the files, remove files aigov wrote earlier that are no longer in the plan, and save the new record (path, tool, and a line-ending-insensitive SHA-256 of each file).

## `sync_configs.py`

Deprecated in 2.0.0. It only runs `aigov.py sync` for repos already on the current layout, and refuses the v1-only flags (`--templates`, `--reconfigure`) with a pointer to the right command.
