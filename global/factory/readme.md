# 🏭 Factory Engine

The dependency-free Node engine behind the three `factory-*` workflows in
[`global/workflows/`](https://github.com/siebe41/ai-governance-starter-kit/blob/main/global/workflows/readme.md).
The sync tool deploys this whole folder to a target repo's `.factory/` whenever
any of those workflows ships.

Operating guide, setup and tuning:
[`docs/factory-playbook.md`](https://github.com/siebe41/ai-governance-starter-kit/blob/main/docs/factory-playbook.md).

<!--
These two links are absolute GitHub URLs, not relative paths, on purpose: this
file is mirrored by `tooling/sync_configs.py`'s `build_factory_target()` into
`.factory/` at a consuming repo's root, two directory levels shallower than
`global/factory/` here — and a vendored repo has no `global/` or `docs/` tree
at all. A relative or repo-root-relative link would break in that deployed
copy. Do not "fix" these back to relative links.
-->

| File | Role |
| :--- | :--- |
| `factory.config.json` | Kit defaults. A repo overrides any subset in its own `.factory.json` at the repo root; unset keys fall through to here. Ships `enabled: false`. |
| `scripts/ledger.mjs` | Durable state on an orphan branch, config loading, pruning. |
| `scripts/governor.mjs` | The admission decision. `--self-test` proves the policy. |
| `scripts/factory.mjs` | Operator + workflow CLI: `status`, `claim`, `record`, `release`, `pause`, `resume`. `--self-test` proves the log parser. |
| `scripts/hostcheck.mjs` | Host capacity preflight — load, available memory, free disk. `--self-test` proves the thresholds. |
| `scripts/retro.mjs` | Weekly report joining the ledger with GitHub outcomes. Read-only by construction — it reports, it never tunes. `--self-test` proves the arithmetic. |

Node 20+ stdlib only — no `npm install`, nothing to audit, nothing to keep
patched. That is deliberate: this code runs with repository credentials on a
schedule, and a dependency tree would be the largest thing to trust in it.

## Why turns, and why a reserve

There is **no public API that reports Claude subscription (Pro/Max) usage.** The
Admin API's usage and cost reports are organisation-scoped and need an Admin API
key; they say nothing about a seat's subscription windows. So the governor cannot
ask how much headroom is left. It keeps its own ledger instead, and treats a
usage-limit error observed by a real run as authoritative over its own
arithmetic — estimate when nothing better is available, ground truth the moment
the service provides it.

Turns are the accounting unit because they are the one cost signal the runner can
observe for every run without an API call. They are a proxy, not a meter: a
turn's real cost varies with context size and thinking depth. Calibrate the
budgets against what you observe in your own repo.

`reserve_fraction` is the knob that matters most. The factory is meant to use
idle capacity, not to race its owner for it — reserving a slice of every window
means sitting down at a terminal in the evening finds headroom waiting rather
than a limit the overnight queue already spent.

## Two guards the workflows add on top

**Billing.** `claude-code-action` resolves its key as `inputs.anthropic_api_key || env.ANTHROPIC_API_KEY` — it reads the *environment* when no input is given, and a self-hosted runner inherits its host's environment. Every model-running factory workflow therefore pins `ANTHROPIC_API_KEY: ""` at job scope and preflights that `CLAUDE_CODE_OAUTH_TOKEN` exists, so a stray key on the box cannot silently move the run onto API billing.

**The machine.** `wip_limit` counts factory work; a self-hosted box also runs CI and everything else it is for. `hostcheck.mjs` asks the host itself, and a busy host **defers** — the claim is released and the issue requeues with nothing consumed and nothing escalated. Being busy is not a failure.

## Verifying a change

Both scripts carry their own assertions and need no repo, branch, or network:

```bash
node .factory/scripts/governor.mjs  --self-test   # admission policy
node .factory/scripts/factory.mjs   --self-test   # execution-log parsing
node .factory/scripts/hostcheck.mjs --self-test   # host capacity thresholds
node .factory/scripts/retro.mjs     --self-test   # retro arithmetic and rendering
```

Run all four after touching any of them. The governor's self-test is the specification of
the admission policy in executable form — if you change a rule, change its
assertion in the same commit.
