# 🔁 Example CI Workflows: Keep Projects on the Current Rules

Two GitHub Actions workflows to copy into a **project** repo's `.github/workflows/`. They keep the project's generated AI governance files (instructions, prompts, agents, skills, MCP config) current with your kit, with no one having to remember to run `aigov.py sync`.

| File | Trigger | What it does |
| :--- | :--- | :--- |
| `aigov-check.yml` | pull requests, pushes to `main`, weekly, manual | Fetches the kit and runs `aigov.py sync --check`. Fails if the generated files are **stale** (the kit changed since the last sync) or **hand-edited**. Changes nothing. `contents: read` only. |
| `aigov-sync.yml` | weekdays, manual | Fetches the kit, runs `aigov.py sync`, and opens (or updates) a pull request with the result. If the repo is already current, it closes any sync pull request left open. Never merges and never passes `--force`. |

They work as a pair. The check tells you a repo has fallen behind, and the sync opens the pull request that fixes it. A kit release then reaches every project as an ordinary pull request that someone there reviews and merges, so a rule change is never applied without a person seeing it.

---

## 🚀 Setup

1. Copy both files into the project's `.github/workflows/`.
2. Set the `AIGOV_KIT_REPO` variable to your kit's `owner/name` (e.g. `acme/ai-governance`). Setting it once as an **organization** variable covers every repo, so the files need no edits. Until it's set, both workflows stop at their first step with a message saying so.
3. If the kit is vendored as a git subtree (QUICKSTART's default, e.g. at `vendor/ai-governance`), also set `AIGOV_VENDOR_PREFIX` to that folder. Leave it unset if CI should read the kit straight from its repo.
4. Add the secrets below if you need them.
5. Run **AI governance sync** once from the Actions tab (`workflow_dispatch`) and confirm it either reports "Already up to date" or opens a pull request.
6. Optionally, make **AI governance check** a required status check in branch protection.

| Name | Kind | Needed when |
| :--- | :--- | :--- |
| `AIGOV_KIT_REPO` | variable | Always. |
| `AIGOV_KIT_REF` | variable | You sync to something other than `main`, e.g. a release tag. |
| `AIGOV_VENDOR_PREFIX` | variable | The kit is vendored as a git subtree. |
| `AIGOV_KIT_TOKEN` | secret | The kit repo is private. Read-only (`Contents: read`) on the kit repo is enough. |
| `AIGOV_SYNC_TOKEN` | secret | Recommended for `aigov-sync.yml`. See the next section. |

### Why the sync wants its own token

Without `AIGOV_SYNC_TOKEN`, the sync falls back to the run's `GITHUB_TOKEN`, which works only partly:

* **A pull request it opens doesn't trigger other workflows**, so `aigov-check.yml` and the project's own CI won't run on the sync pull request until someone pushes to it.
* **It can't push changes under `.github/workflows/`.** The `claude-code` target writes the factory workflows there, so a kit release that changes one makes the sync's push fail.
* **It can open pull requests only if** Settings > Actions > General > "Allow GitHub Actions to create and approve pull requests" is on.

Use a GitHub App installation token or a fine-grained PAT scoped to the project repo, with **Contents**, **Pull requests**, and **Workflows** set to read/write. A Copilot-only repo with that setting on can get by without one, but its sync pull requests won't run CI.

---

## 🧭 How Each Mode Works

**Kit read from its repo** (`AIGOV_VENDOR_PREFIX` unset): both workflows check out the project and the kit side by side and run the kit's `aigov.py` against the project. There is no copy of the kit in the project, so "stale" means "differs from the kit at `AIGOV_KIT_REF` right now".

**Kit vendored as a subtree** (`AIGOV_VENDOR_PREFIX` set): the check runs the project's **own** vendored `aigov.py`, so it confirms the generated files match the kit version committed in the project. It then compares that vendored copy with upstream and fails if they differ. The sync runs `git subtree pull --squash` from the fetched kit before running `aigov.py sync`, so one pull request updates both the vendored kit and the files generated from it. If someone has edited files inside the vendored kit, the subtree pull conflicts and the sync stops; project-specific rules belong in `local_dirs`, not in the vendored copy.

**Kit as a git submodule:** leave `AIGOV_VENDOR_PREFIX` unset. The check then works against upstream as described above, and the sync updates the generated files but not the submodule pointer, which you bump yourself.

---

## ⚖️ Things to Decide

* **Blocking pull requests on a kit release.** Out of the box, a kit release makes `aigov-check` fail on every open pull request in every project until that project merges its sync pull request. That is the point if you want every repo on the current rules, and the sync pull request is already waiting when it happens. If it's too strict, set `AIGOV_KIT_REF` to a release tag and move it on your own schedule, or don't make the check required.
* **Hand edits fail both workflows on purpose.** aigov can't tell whether a hand edit to a generated file should be kept, so it refuses, and so do these workflows. The fix is to move the change into the kit or a `local_dirs` folder, then undo it in the generated file. `--force` would silently throw the edit away, which is why the sync never uses it.
* **The `aigov-sync/<base>` branch belongs to the workflow.** It's force-pushed whenever the result changes, and rebuilt on the latest base each time. Push any fixes to the base branch instead, or close the pull request and sync by hand.

---

## 🔒 Security Notes

These workflows run the kit's `aigov.py` with the project's credentials, so `global/workflows/readme.md`'s rules apply here too:

* **`aigov-check.yml` is read-only** (`contents: read`, `persist-credentials: false` on both checkouts), so it's safe on pull requests from forks. Fork pull requests don't receive `AIGOV_KIT_TOKEN`, though, so with a private kit they can't fetch it and the check fails for them.
* **`aigov-sync.yml` writes.** Its token can push branches and open pull requests, and with `Workflows: write` it can change CI. It only runs on a schedule or by hand, never on a pull request, and the code it runs comes from your kit repo. That makes **write access to the kit** the real control: anyone who can merge into the kit can change what runs here. Protect the kit's default branch, or set `AIGOV_KIT_REF` to a reviewed tag.
* **No untrusted input reaches a shell.** The scripts use only the repository variables above, the kit's own output, and git metadata. No issue or pull request text is used.
* The only actions used are GitHub's own (`actions/checkout`, `actions/setup-python`), plus the `gh` CLI that comes on GitHub-hosted runners.

---

## 🤔 Why These Aren't in `global/workflows/`

Files in `global/workflows/` are deployed by aigov, and only for the `claude-code` target. These two belong in every project, Copilot ones included. A deployed sync workflow would also be overwriting its own file on every run. So they live here, and you copy them in by hand once. aigov never touches them, since it only manages files it wrote.
