#!/usr/bin/env python3
"""
Deprecated in v2.0.0: use tooling/aigov.py (install / sync / migrate / status).

Kept for one release so existing scripts don't break. It only ever runs
`aigov.py sync`, and only for repos already on v2. It never guesses which AI
tool a repo uses; v1 repos and fresh repos are told which command to run.
"""
import subprocess
import sys
from pathlib import Path

AIGOV = Path(__file__).resolve().parent / "aigov.py"

print("sync_configs.py is deprecated; use `python tooling/aigov.py sync` (or install / migrate).",
      file=sys.stderr)
passthrough = []
args = sys.argv[1:]
for i, arg in enumerate(args):
    if arg in ("-o", "--output") and i + 1 < len(args):
        passthrough += ["--output", args[i + 1]]
    elif arg.startswith("--output="):
        passthrough.append(arg)
    elif arg in ("-t", "--templates", "--reconfigure"):
        print("aigov stopped: --templates and --reconfigure are gone in v2. Use `aigov.py install` for a "
              "new repo or `aigov.py migrate` to change tools; edit `templates` in .ai-governance.json "
              "and run `aigov.py sync` to change overlays.", file=sys.stderr)
        sys.exit(2)
sys.exit(subprocess.call([sys.executable, str(AIGOV), "sync", *passthrough]))
