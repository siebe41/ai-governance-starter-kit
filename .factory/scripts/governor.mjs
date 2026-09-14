/**
 * Admission control: decides how many tasks, if any, the factory may start now.
 *
 * ## Why this exists rather than "just poll the usage API"
 *
 * There is no public endpoint that reports Claude **subscription** (Pro/Max)
 * usage. The Admin API's usage and cost reports are organisation-scoped and
 * require an Admin API key; they say nothing about a seat's subscription
 * windows. So the governor cannot ask how much headroom is left — it has to
 * account for its own consumption and, crucially, believe the model over its
 * own arithmetic the moment the two disagree.
 *
 * That gives two signals, in strict priority order:
 *
 *   1. **Observed limit (authoritative).** When a worker run is refused for
 *      usage limits, it records the reset time it was given. Until that time
 *      passes, admission is zero regardless of what the estimate says. This is
 *      ground truth: it came from the service, not from a guess.
 *   2. **Estimated usage (advisory).** Turns consumed by factory runs inside the
 *      rolling window and the trailing week, compared against configured
 *      budgets. Deliberately conservative, and deliberately *not* the whole
 *      budget — see `reserve_fraction`.
 *
 * `reserve_fraction` is the point of the whole design. The factory is meant to
 * use the subscription's idle capacity, not to race its owner for it. Reserving
 * a slice of every window means that sitting down at a terminal at 9pm finds
 * headroom waiting rather than a limit the overnight queue already spent. Set it
 * to 0 only if nothing else shares the subscription.
 *
 * Turns are the unit because they are the one cost signal the runner can observe
 * for every run without an API call. They are a proxy, not a meter: a turn's real
 * cost varies with context size and thinking depth. Treat the budgets as dials
 * calibrated against observed behaviour in your own repo, not as physical units.
 */

import { loadConfig, pruneInFlight, pruneRuns, readState } from "./ledger.mjs";

const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * HOUR_MS;

/** Sums turns across runs started within `sinceMs` of `now`. */
export function turnsSince(runs, now, sinceMs) {
  const cutoff = now - sinceMs;
  return (runs ?? [])
    .filter((run) => Date.parse(run.started_at ?? 0) >= cutoff)
    .reduce((total, run) => total + (Number(run.turns) || 0), 0);
}

function inQuietHours(now, quietHoursUtc) {
  if (!Array.isArray(quietHoursUtc) || quietHoursUtc.length === 0) return false;
  return quietHoursUtc.includes(new Date(now).getUTCHours());
}

/**
 * Pure admission decision. Everything it needs is an argument, so the whole
 * policy is testable without a repo, a branch, or a network — see `--self-test`.
 *
 * Returns `{ admit, reason, detail }` where `admit` is a count, never a boolean:
 * the conductor may be allowed to start two tasks on a tick where the queue has
 * five, and "how many" is the governor's call, not the conductor's.
 */
export function decide({ config, state, now = Date.now(), queueDepth = 0 }) {
  const gov = config.governor;
  const adm = config.admission;
  const detail = {};

  if (!config.enabled) {
    return { admit: 0, reason: "factory is disabled (`enabled: false` in .factory.json)", detail };
  }
  if (state.paused) {
    return { admit: 0, reason: "factory is paused by an operator (state.paused)", detail };
  }

  // 1. Observed limit wins over every estimate below it.
  const resetsAt = state.limit?.resets_at ? Date.parse(state.limit.resets_at) : null;
  if (resetsAt && resetsAt > now) {
    detail.limit_resets_at = new Date(resetsAt).toISOString();
    const minutes = Math.ceil((resetsAt - now) / 60000);
    return {
      admit: 0,
      reason: `usage limit observed at ${state.limit.hit_at}; holding ${minutes} more minute(s) until ${detail.limit_resets_at}`,
      detail,
    };
  }

  if (inQuietHours(now, adm.quiet_hours_utc)) {
    return { admit: 0, reason: `inside quiet hours (UTC hour ${new Date(now).getUTCHours()})`, detail };
  }

  const inFlight = (state.in_flight ?? []).length;
  detail.in_flight = inFlight;
  detail.wip_limit = adm.wip_limit;
  if (inFlight >= adm.wip_limit) {
    return { admit: 0, reason: `WIP limit reached (${inFlight}/${adm.wip_limit} in flight)`, detail };
  }

  if (queueDepth <= 0) {
    return { admit: 0, reason: "nothing in the queue", detail };
  }

  // 2. Estimated usage, with the operator's reserve held back.
  const usable = 1 - Number(gov.reserve_fraction || 0);
  const windowUsed = turnsSince(state.runs, now, gov.window_hours * HOUR_MS);
  const windowCap = gov.window_turn_budget * usable;
  detail.window = { used: windowUsed, cap: Math.round(windowCap), hours: gov.window_hours };
  if (windowUsed >= windowCap) {
    return {
      admit: 0,
      reason: `rolling ${gov.window_hours}h budget spent (${windowUsed}/${Math.round(windowCap)} turns, ${Math.round(gov.reserve_fraction * 100)}% reserved for interactive use)`,
      detail,
    };
  }

  const weekUsed = turnsSince(state.runs, now, 7 * DAY_MS);
  const weekCap = gov.weekly_turn_budget * usable;
  detail.weekly = { used: weekUsed, cap: Math.round(weekCap) };
  if (weekUsed >= weekCap) {
    return {
      admit: 0,
      reason: `weekly budget spent (${weekUsed}/${Math.round(weekCap)} turns)`,
      detail,
    };
  }

  const admit = Math.min(adm.wip_limit - inFlight, adm.max_admissions_per_tick, queueDepth);
  return {
    admit,
    reason: `admitting ${admit} (window ${windowUsed}/${Math.round(windowCap)} turns, week ${weekUsed}/${Math.round(weekCap)}, ${inFlight}/${adm.wip_limit} in flight)`,
    detail,
  };
}

/**
 * Turns a usage-limit failure into a hold. `resetsAt` is whatever the run could
 * actually parse out of the failure; when nothing usable was found the caller
 * passes null and we fall back to a configured cooldown rather than guessing a
 * precise time we do not have.
 */
export function recordLimit(state, { resetsAt, source, now = Date.now(), cooldownMinutes }) {
  const resolved = resetsAt && Number.isFinite(Date.parse(resetsAt))
    ? new Date(Date.parse(resetsAt))
    : new Date(now + cooldownMinutes * 60000);
  state.limit = {
    hit_at: new Date(now).toISOString(),
    resets_at: resolved.toISOString(),
    source,
    inferred: !resetsAt,
  };
  return state;
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes("--self-test")) return selfTest();

  const queueDepth = Number(readFlag(args, "--queue-depth") ?? 0);
  const config = loadConfig();
  let state = readState(config.state_branch);
  state = pruneRuns(state, config.governor.ledger_retention_days);
  ({ state } = pruneInFlight(state));

  const decision = decide({ config, state, queueDepth });
  const payload = { ...decision, config: { wip_limit: config.admission.wip_limit, dry_run: config.dry_run } };
  console.log(JSON.stringify(payload, null, 2));

  if (process.env.GITHUB_OUTPUT) {
    const { appendFileSync } = await import("node:fs");
    appendFileSync(
      process.env.GITHUB_OUTPUT,
      `admit=${decision.admit}\nreason=${decision.reason.replace(/\n/g, " ")}\n`,
    );
  }
}

function readFlag(args, name) {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : undefined;
}

/** Assertions over the policy above. Runs with no repo, no network, no branch. */
async function selfTest() {
  const assert = await import("node:assert/strict");
  const now = Date.parse("2026-09-14T12:00:00Z");
  const base = {
    enabled: true,
    admission: { wip_limit: 2, max_admissions_per_tick: 1, quiet_hours_utc: [] },
    governor: {
      window_hours: 5,
      window_turn_budget: 100,
      weekly_turn_budget: 1000,
      reserve_fraction: 0.3,
      ledger_retention_days: 30,
    },
  };
  const empty = { runs: [], in_flight: [], limit: null, paused: false };
  const run = (minutesAgo, turns) => ({ started_at: new Date(now - minutesAgo * 60000).toISOString(), turns });

  assert.equal(decide({ config: { ...base, enabled: false }, state: empty, now, queueDepth: 5 }).admit, 0,
    "disabled factory admits nothing");
  assert.equal(decide({ config: base, state: { ...empty, paused: true }, now, queueDepth: 5 }).admit, 0,
    "paused factory admits nothing");
  assert.equal(decide({ config: base, state: empty, now, queueDepth: 0 }).admit, 0,
    "empty queue admits nothing");
  assert.equal(decide({ config: base, state: empty, now, queueDepth: 5 }).admit, 1,
    "healthy state admits up to max_admissions_per_tick");

  const limited = { ...empty, limit: { hit_at: "x", resets_at: new Date(now + HOUR_MS).toISOString() } };
  assert.equal(decide({ config: base, state: limited, now, queueDepth: 5 }).admit, 0,
    "an unexpired observed limit blocks admission");
  const expired = { ...empty, limit: { hit_at: "x", resets_at: new Date(now - HOUR_MS).toISOString() } };
  assert.equal(decide({ config: base, state: expired, now, queueDepth: 5 }).admit, 1,
    "an expired observed limit stops blocking");

  // 70 turns against a 100-turn window with 30% reserved == exactly spent.
  const spent = { ...empty, runs: [run(60, 40), run(120, 30)] };
  assert.equal(decide({ config: base, state: spent, now, queueDepth: 5 }).admit, 0,
    "reserve_fraction is held back from the window budget");
  const aged = { ...empty, runs: [run(60 * 6, 40), run(60 * 7, 30)] };
  assert.equal(decide({ config: base, state: aged, now, queueDepth: 5 }).admit, 1,
    "turns outside the rolling window do not count against it");

  const full = { ...empty, in_flight: [{ issue: 1 }, { issue: 2 }] };
  assert.equal(decide({ config: base, state: full, now, queueDepth: 5 }).admit, 0,
    "WIP limit caps admission");

  const quiet = { ...base, admission: { ...base.admission, quiet_hours_utc: [12] } };
  assert.equal(decide({ config: quiet, state: empty, now, queueDepth: 5 }).admit, 0,
    "quiet hours block admission");

  const weekly = { ...empty, runs: [run(60 * 24 * 2, 700)] };
  assert.equal(decide({ config: base, state: weekly, now, queueDepth: 5 }).admit, 0,
    "weekly budget is enforced independently of the window");

  const inferred = recordLimit({ ...empty }, { resetsAt: null, source: "worker#1", now, cooldownMinutes: 300 });
  assert.equal(inferred.limit.inferred, true, "an unparseable reset time is marked inferred");
  assert.equal(inferred.limit.resets_at, new Date(now + 300 * 60000).toISOString(),
    "an unparseable reset time falls back to the configured cooldown");

  console.log("governor self-test: all assertions passed");
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error);
    process.exit(1);
  });
}
