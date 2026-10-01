# 🛠️ Deployment Tooling

## `aigov.py`

Writes this kit's assets into a project repo for the AI tool(s) that repo uses. Python 3.9+, standard library only.

```bash
python tooling/aigov.py install   --output path/to/project   # asks: which AI tool? which overlays?
python tooling/aigov.py sync      --output path/to/project   # re-apply the kit; never asks
python tooling/aigov.py sync --check                        # CI: fail if out of date or hand-edited
python tooling/aigov.py migrate   --output path/to/project   # change/add tools, or move a v1 repo
python tooling/aigov.py status    --output path/to/project   # what's installed, per file
```

For CI, [`examples/workflows/`](/examples/workflows/readme.md) has a check workflow (`sync --check` against a freshly fetched kit) and a scheduled sync workflow that opens a pull request.

`--output` defaults to the current folder. For scripts and CI, pass answers as flags: `--targets copilot claude-code`, `--templates UI` (or `--templates` alone for none), and `--yes` for `migrate`.

Where each item lands, and why, is in [`TARGETS.md`](/TARGETS.md). What aigov refuses to do is in the main `README.md` under "What aigov refuses to do".

## How it works

1. **Plan.** Build the full list of files to write from `global/`, the selected `templates/`, and the project's `local_dirs`, for the selected targets only.
2. **Check.** Compare the plan against the project and the record in `.ai-governance.json`. Any file that exists but wasn't written by aigov, or was written by aigov and then edited, stops the run before anything changes.
3. **Apply.** Write the files, remove files aigov wrote earlier that are no longer in the plan, and save the new record (path, target, and a line-ending-insensitive SHA-256 of each file).

## `sync_configs.py`

Deprecated in 2.0.0 and kept for one release. It only runs `aigov.py sync` for repos already on v2, and refuses the v1-only flags (`--templates`, `--reconfigure`) with a pointer to the right command.
