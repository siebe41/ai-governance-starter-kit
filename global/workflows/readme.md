# ⚙️ GitHub Workflows

Canonical GitHub Actions workflow files, deployed by `tooling/aigov.py`
into a target repo's `.github/workflows/` (Claude Code target only — the shipped
workflows run `claude-code-action`).

This is the category for governance that has to run **whether or not anyone
opens an editor**. `instructions/` is a policy a model reads; `hooks/` is a rule
the harness enforces during a session; a workflow is a rule that runs on a
schedule, on a webhook, or on a push, with no session involved at all.

---

## 📄 Included Workflows

The three files here are one system — the **factory**: a governed loop that
turns GitHub issues into reviewable pull requests on whatever capacity your
Claude subscription has spare, and files its own work through scheduled audits.

| File | Trigger | What it does |
| :--- | :--- | :--- |
| `factory-conductor.yml` | hourly cron | Asks the governor whether there is headroom, picks that many issues off the queue, claims each in the ledger, dispatches a worker. Runs no model itself. |
| `factory-worker.yml` | dispatched by the conductor | Runs **one** issue under a turn allowance and a deadline, then opens a pull request or escalates. Records the outcome in the ledger. |
| `factory-audit.yml` | daily cron | Runs a read-only audit (security, accessibility, SEO, dependencies, docs drift) and files findings as issues into the same queue. Changes no code. |
| `factory-retro.yml` | weekly cron | Joins the ledger with what GitHub says happened to those issues and publishes a report. `contents: read` + `issues: read` only — it **reports, it never tunes**. |

They depend on the engine in [`global/factory/`](../factory/readme.md), which
aigov deploys to `.factory/` whenever any `factory-*` workflow ships. Full
setup, tuning, and operating notes: [`docs/factory-playbook.md`](../../docs/factory-playbook.md).

**They ship inert.** The default config sets `enabled: false`, so deploying them
into a repo starts nothing until someone writes a `.factory.json` that turns the
factory on. Excluding all three (via `.ai-governance.json`'s
`exclude.workflows`) also suppresses the engine, so a repo that does not want a
factory gets no stray `.factory/` directory either.

The remaining three are independent, unconditional checks — no subscription,
no engine, no config file to turn them on:

| File | Trigger | What it does |
| :--- | :--- | :--- |
| `secret-scan.yml` | every push to `main` and every pull request | Runs [`gitleaks`](https://github.com/gitleaks/gitleaks) over the diff and fails if it finds a hardcoded credential. The workflow's header comment documents swapping in [Betterleaks](https://github.com/betterleaks/betterleaks) — gitleaks' own successor, faster and lower-noise with a compatible config format — as a drop-in alternative; it isn't the default because its GitHub Action is third-party-maintained rather than published by the tool's own org. |
| `check-contradictory-instructions.yml` | a pull request touching `.github/copilot-instructions.md`, `.github/instructions/`, `CLAUDE.md`, or `AGENTS.md` | A heuristic scan for directive pairs that assert and then negate the same thing (`Always use tabs` / `Never use tabs`), so two rules don't silently disagree with each other. |
| `check-stale-instructions.yml` | every pull request, every push to `main` | Scans the same instruction files for markdown links and backtick-quoted paths that point at a file no longer in the repo — the usual symptom of a rename or delete that didn't also update the doc pointing at it. |

Both instruction checks only look at the files `TARGETS.md` documents as
instruction output (`.github/copilot-instructions.md`,
`.github/instructions/`, `CLAUDE.md`, `AGENTS.md`), so they are a no-op in a
repo — like this one — that authors instructions elsewhere (`global/`) rather
than deploying them; they start finding real issues the moment a project
installs this kit and gets those files for real. Both are **heuristics, not
provers**: each is scoped to catch its one failure mode cheaply, not to
understand prose, so read every finding rather than trusting the check blindly
— see the comment at the top of each workflow for exactly what it does and
does not catch.

---

## 🔒 A Workflow Runs Arbitrary Code With Repository Credentials

Like `hooks/`, and unlike every category a model merely reads, these assets
execute — here with a `GITHUB_TOKEN`, a `permissions` block, and access to
whatever secrets the repo holds. `global/instructions/00-security-governance.md`
applies with full force:

* **Read any workflow in full before vendoring it.** Every `uses:` line is code
  you are granting repository credentials to.
* **Pin the `permissions` block to what the workflow actually needs.** The
  factory workflows declare theirs explicitly and narrowly; keep it that way.
* **Never write a workflow that pipes untrusted input into a shell.** Issue
  titles and bodies are attacker-controllable in a public repo. The factory
  workflows pass issue text through `actions/github-script` outputs and the model
  prompt, never through `run:` interpolation.
* **Prefer a fixed path to a discovered one.** `.factory/` is hardcoded in the
  workflows precisely so a stray copy of the kit elsewhere in the tree cannot be
  picked up and executed instead.

---

## 🚀 Deployment Behavior

`.github/workflows/` is a directory a target repo already owns and fills with its
own CI, so aigov only ever touches the files it wrote there:

1. Only `*.yml` / `*.yaml` files in `global/workflows/` (plus any selected
   template's `workflows/` and any `local_dirs` override) are read — `readme.md`
   is skipped naturally.
2. Each is copied in by name and recorded in `.ai-governance.json`. A repo's own
   `ci.yml`, `release.yml`, and anything else already there is never read,
   changed, or deleted. If a repo already has a hand-written file with the same
   name as a kit workflow, the run stops rather than overwrite it.
3. Excluding a workflow (`exclude.workflows`, by filename or stem) removes the
   copy aigov wrote on the next `sync`. Excluding every `factory-*` workflow
   removes the `.factory/` engine too.

---

## ➕ Adding Your Own Workflow

1. Drop `global/workflows/<name>.yml` in this folder.
2. Give it an explicit, minimal `permissions:` block. The default for a repo that
   has not set one org-wide is far wider than most workflows need.
3. Prove it on a branch before vendoring it — `workflow_dispatch` with a dry-run
   input is the cheapest way to make a scheduled workflow testable.
4. Add it to the **Included Workflows** table above.
5. For a workflow you don't want maintained centrally, use `local_dirs.workflows`
   in `.ai-governance.json` instead of editing this folder — see the top-level
   `README.md`'s "Include/Exclude & Bring Your Own".
