# 🏭 The Factory Playbook

A governed loop that turns GitHub issues into reviewable pull requests on
whatever capacity your Claude subscription has spare, and keeps its own queue fed
through scheduled audits.

It is assembled from parts this kit already ships:

| Part | Where |
| :--- | :--- |
| Three workflows | [`global/workflows/`](../global/workflows/readme.md) → `.github/workflows/` |
| The engine | [`global/factory/`](../global/factory/readme.md) → `.factory/` |
| Standing rules | `global/instructions/05-autonomous-factory.md` → `CLAUDE.md` |
| Run procedures | `global/skills/factory-task/`, `factory-audit/` → `.claude/skills/` |
| Per-repo settings | your own `.factory.json` at the repo root |

---

## 🧭 What it does

```text
                 scheduled audits                    humans
              (read-only, file issues)          (file issues)
                        │                             │
                        └──────────┐      ┌───────────┘
                                   ▼      ▼
                          ┌─────────────────────┐
                          │  queue: open issues │
                          │  labelled `factory` │
                          └──────────┬──────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │   CONDUCTOR  (hourly cron)      │
                    │   • governor: is there headroom?│
                    │   • claim a slot in the ledger  │
                    │   • dispatch one worker         │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │   WORKER  (one issue, capped)   │
                    │   turn allowance + deadline     │
                    └────────┬───────────────┬────────┘
                             │               │
                      pull request       escalation
                             │               │
                             ▼               ▼
                        a human reviews and decides
```

Two things are load-bearing and worth stating plainly:

* **Nothing merges itself.** Every run ends at a human.
* **The governor, not the cron, decides whether work starts.** The schedule is
  deliberately dumber than the policy — tune the budgets, not the cron line.

---

## ⚙️ Turning it on

### 1. Deploy the assets

```bash
python tooling/sync_configs.py --output /path/to/your-repo
```

This writes the three workflows, the `.factory/` engine, the instructions into
`CLAUDE.md`, and the two skills. **Nothing runs yet** — the shipped default is
`enabled: false`.

### 2. Provide the credential

Add a repository secret **`CLAUDE_CODE_OAUTH_TOKEN`**. This is what makes the
factory run on your Claude subscription rather than on metered API credit.
Generate it with `claude setup-token` and store it under
*Settings → Secrets and variables → Actions*.

### 3. Choose where it runs

Set the repository **variable** `FACTORY_RUNNER`:

| Value | Effect |
| :--- | :--- |
| unset | GitHub-hosted `ubuntu-latest` |
| `"ubuntu-latest"` | the same, explicitly |
| `["self-hosted","nas","factory"]` | your own runner pool |

It is a variable rather than a `.factory.json` key because `runs-on` is evaluated
before any step can read a file.

If the factory **must** run on your own hardware, also set
`"require_self_hosted": true` in `.factory.json`. Every factory job then fails
fast on a GitHub-hosted runner rather than quietly running there and spending
Actions minutes — `runner.environment` is `github-hosted` or `self-hosted`, and
the preflight checks it.

> **Give the factory its own runner labels.** A long factory run in the same pool
> as your CI will queue pull-request checks behind it. Dedicated labels, not
> shared capacity.

### 4. Create the labels

`factory` (the queue), plus `factory:in-flight`, `factory:escalated`,
`factory:audit`, and optionally `factory:mechanical` / `factory:deep` to set a
task class when filing.

### 5. Write `.factory.json` and start in dry-run

```json
{
  "enabled": true,
  "dry_run": true,
  "admission": { "wip_limit": 1, "max_admissions_per_tick": 1 },
  "governor": { "reserve_fraction": 0.4 }
}
```

`dry_run` makes the conductor report what it *would* admit without dispatching
anything. Leave it there for a day or two. Read the job summaries. You are
checking that the queue contains what you expect and the governor's arithmetic
matches your sense of your own usage — not that the model is any good yet.

### 6. Let one real task through

Set `"dry_run": false` with `wip_limit: 1`. Label exactly one small, well-specified
issue `factory` and `factory:mechanical`. Watch the whole path: admission,
claim, run, pull request, ledger record.

Then raise the limits slowly. The failure mode of this system is not a bad pull
request — it is twenty of them arriving at once with nobody willing to read the
twenty-first.

---

---

## 💳 The billing guard

The factory is designed to run on a Claude **subscription**, never at API rates.
Two things enforce that rather than assume it:

**The OAuth token is required.** Every factory job preflights
`CLAUDE_CODE_OAUTH_TOKEN` and fails with a clear message if it is missing —
instead of starting a run that might authenticate some other way.

**`ANTHROPIC_API_KEY` is pinned empty at job scope.** This one is not
theoretical. `claude-code-action` resolves its key as:

```yaml
ANTHROPIC_API_KEY: ${{ inputs.anthropic_api_key || env.ANTHROPIC_API_KEY }}
```

— it reads the **environment** when no input is given. A self-hosted runner
inherits its host's environment, so an `ANTHROPIC_API_KEY` present on that box
for something else entirely would be forwarded into the run, and the action's own
docs note that a static credential takes precedence over other auth. Pinning it
empty in the job's `env:` means the only credential that can reach the run is the
OAuth token.

The conductor carries neither guard, because it runs no model at all.

---

## 🖥️ Not overloading the box

`wip_limit` counts **factory** work. A self-hosted runner shares its machine with
CI, a container swarm, databases — everything else that box is for — and the
factory can see none of it. Two workers under a WIP limit of two will start
happily on a host already at load 30 because of a CI storm, and what suffers is
not the factory: it is the pull-request checks and interactive work queued behind
it.

So capacity is also asked of the **machine**:

```json
"host": {
  "enabled": true,
  "max_load_per_cpu": 0.7,
  "min_free_memory_mb": 2048,
  "min_free_disk_gb": 10
}
```

**A busy host defers, it does not fail.** The worker releases its claim, the
issue returns to the queue with nothing consumed, and nothing is escalated —
being busy is not a failure, and must not cost an issue its budget or a human's
attention. The conductor checks too, so a loaded box does not produce an
admit-then-immediately-defer churn every hour.

Three notes on the implementation:

* It reads **`MemAvailable`**, not `MemFree`. Page cache is reclaimable and
  `MemFree` on a healthy Linux box is near zero by design — checking it would
  defer every run forever.
* It reads `/proc/loadavg` directly rather than `os.loadavg()`, which returns
  `[0,0,0]` on platforms with no load concept and would read as a perfectly idle
  machine.
* **Unknown never means unhealthy.** Any probe that cannot be read is skipped
  rather than blocking work on a host it knows nothing about. On non-Linux it
  reports "ok" — this is a guard, not a gate.

If several runners share one physical machine, remember each sees the *whole*
host's load, so they will defer together. That is the intent: the limit is the
machine, not the runner.

---

## 🎛️ Tuning the governor

```json
"governor": {
  "window_hours": 5,
  "window_turn_budget": 400,
  "weekly_turn_budget": 4000,
  "reserve_fraction": 0.3,
  "default_cooldown_minutes": 300,
  "ledger_retention_days": 30
}
```

**`reserve_fraction` is the knob that matters.** It is the share of every budget
the factory refuses to touch, held for you. At `0.3` the factory will spend at
most 70% of a window and then stop, so sitting down at a terminal in the evening
finds headroom waiting rather than a limit the overnight queue already spent. Set
it to `0` only if nothing else draws on the subscription.

**Turns are a proxy, not a meter.** A turn's real cost varies with context size
and thinking depth, so the budgets are dials you calibrate against observed
behaviour in your own repo, not physical units. Start conservative. After a week,
compare `weekly_turn_budget` against what the ledger actually recorded and adjust.

**There is no usage API to check against.** No public endpoint reports Claude
subscription (Pro/Max) usage — the Admin API's usage and cost reports are
organisation-scoped and need an Admin API key. So the governor keeps its own
ledger and, when a run is actually refused for usage limits, records the reset
time and holds admission until it passes. Observed limits always beat the
estimate; when a refusal carries no parseable reset time, it falls back to
`default_cooldown_minutes` rather than inventing one.

**Quiet hours** (`admission.quiet_hours_utc: [8, 9, 10]`) keep the factory out of
the hours you actually work, if you would rather have all of your capacity then
instead of a reserved slice.

---

## 📋 Task classes

```json
"admission": {
  "task_classes": {
    "mechanical": { "max_turns": 15, "deadline_minutes": 30 },
    "standard":   { "max_turns": 40, "deadline_minutes": 90 },
    "deep":       { "max_turns": 80, "deadline_minutes": 180 }
  },
  "allowed_task_classes": ["mechanical", "standard"]
}
```

A class is set by labelling an issue `factory:mechanical` or `factory:deep`;
unlabelled work is `standard`. `deep` is deliberately absent from
`allowed_task_classes` by default — the expensive class should be a decision, not
a default, and a worker dispatched with a class the repo has not enabled refuses
before it starts.

**Start with mechanical work.** Documentation drift, dependency bumps, a stale
comment, a missing test for existing behaviour. These are cheap, they are easy to
review, and they let you build trust in the loop before you point it at anything
that requires judgement.

---

## 🔍 Audits

Every audit ships disabled. Turn on **one**:

```json
"audits": {
  "docs-drift": { "enabled": true, "cron": "0 4 * * 5", "task_class": "mechanical", "max_issues": 3 }
}
```

`docs-drift` is the best first one: it is cheap, its findings are easy to verify,
and drift compounds silently — every future agent run reads those docs as if they
were true.

An audit files issues and changes nothing. That indirection is the point: a
finding goes through the same admission control, budget and human review as any
other work, and you get to read it before a line changes. `max_issues` is a hard
cap per run, because the way this feature dies is a flood of low-value issues
nobody wants to triage.

Only the **day-of-week** field of an audit's cron is read — the workflow fires
once daily and each audit decides whether today is its day. The hour and minute
are documentation.

---

## 🛠️ Operating it

```bash
node .factory/scripts/factory.mjs status     # what the governor would decide now
node .factory/scripts/factory.mjs pause --reason "release week"
node .factory/scripts/factory.mjs resume
node .factory/scripts/factory.mjs release --issue 123   # free a stuck slot
```

`pause` stops admission; work already in flight still finishes. Paused state
lives in the ledger, so it survives across runs until someone resumes it.

### The ledger

State lives as `state.json` on an orphan branch (`factory-state` by default):
runs, in-flight claims, and any observed usage limit. A branch rather than a
database because it needs no infrastructure, is already authenticated by the
workflow's own token, works in any repo that vendors this kit — and gives you a
git history of everything the factory did while nobody was watching.

A worker killed mid-run (runner reboot, cancelled job) never clears its own
claim, so entries are pruned once their deadline passes. Without that, a dead
task would hold a WIP slot forever and the factory would go quiet while looking
busy.

---

## ✅ Verifying a change to the engine

```bash
node .factory/scripts/governor.mjs --self-test
node .factory/scripts/factory.mjs  --self-test
```

No repo, branch or network needed. The governor's self-test is the admission
policy written as executable assertions — change a rule, change its assertion in
the same commit.

---

## 🧯 What to watch for in the first weeks

* **Escalations that repeat.** The same issue escalating twice means the issue is
  underspecified, not that the worker is weak. Rewrite the issue or close it.
* **Runs that burn the allowance before producing anything.** Usually a task
  class set too low for the work, or an issue that needed a decision nobody made.
* **Pull requests nobody reviews.** Lower `wip_limit`. An unreviewed queue is the
  signal that the factory is producing faster than it is producing *value*.
* **`LEARNINGS.md` growing without being read.** Entries should be durable rules,
  not a run log. If it has become a diary, prune it — a padded learnings file
  stops being read, and then it stops working.

---

## 🙏 Prior art

The shape here — a queue with admission control, per-run budgets with mid-run
re-authorisation, escalation instead of self-merge, and a durable fact ledger fed
by the runs themselves — follows the **Ember Software Factory**
([jomcgi.dev/slop/factory](https://jomcgi.dev/slop/factory)), which runs this
pattern against a live monorepo and publishes its own numbers. This kit's version
is deliberately smaller: no microVMs, no custom control plane, no bespoke
knowledge-graph service — just GitHub Actions, a branch, and the learnings log
this kit already ships.
