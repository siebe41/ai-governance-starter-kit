/**
 * Operator + workflow CLI over the factory ledger.
 *
 *   node factory.mjs status                       — what the governor would decide right now
 *   node factory.mjs claim   --issue N --run-id R --deadline-minutes M --task-class C
 *   node factory.mjs record  --issue N --run-id R --outcome landed|escalated|failed|limited \
 *                            [--execution-file PATH] [--turns N]
 *   node factory.mjs release --issue N            — drop an in-flight entry without a run record
 *   node factory.mjs pause  [--reason "..."]      — stop admitting; in-flight work still finishes
 *   node factory.mjs resume
 *
 * `claim` is what makes the WIP limit real: the conductor writes the in-flight
 * entry *before* dispatching the worker, so a second conductor tick that fires
 * while the first worker is still starting up sees the slot as taken. Claiming
 * after dispatch would leave a window where both ticks read the same free slot.
 */

import { existsSync, readFileSync } from "node:fs";
import { loadConfig, pruneInFlight, pruneRuns, readState, updateState } from "./ledger.mjs";
import { decide, recordLimit } from "./governor.mjs";

/**
 * Pulls what we can from the Claude Code action's execution log.
 *
 * The log's exact shape is owned by `anthropics/claude-code-action` and is not a
 * contract this kit controls, so every field here is best-effort: a missing or
 * restructured log degrades to `turns: null` rather than throwing, and the run is
 * still recorded. A run whose turn count cannot be read is charged the task
 * class's full allowance instead of zero — under-counting would let a broken
 * parser quietly disable the whole budget, which is the one failure mode that
 * matters here. Over-counting merely makes the factory too cautious.
 */
export function parseExecution(raw) {
  const result = { turns: null, cost_usd: null, limited: false, resets_at: null };
  if (!raw) return result;

  let parsed = null;
  try {
    parsed = JSON.parse(raw);
  } catch {
    /* not JSON — fall through to the text scan below */
  }

  const visit = (node) => {
    if (!node || typeof node !== "object") return;
    if (Array.isArray(node)) return node.forEach(visit);
    for (const [key, value] of Object.entries(node)) {
      const k = key.toLowerCase();
      if (result.turns === null && /^(num_turns|turns|turn_count)$/.test(k) && Number.isFinite(Number(value))) {
        result.turns = Number(value);
      }
      if (result.cost_usd === null && /cost_usd|total_cost/.test(k) && Number.isFinite(Number(value))) {
        result.cost_usd = Number(value);
      }
      visit(value);
    }
  };
  visit(parsed);

  // Usage-limit detection is text-level on purpose: the phrasing travels in an
  // error string, and matching the string is more durable than guessing which
  // envelope field of the day carries it.
  const text = typeof raw === "string" ? raw : JSON.stringify(parsed ?? "");
  if (/usage limit|rate.?limit|quota exceeded|429/i.test(text)) {
    result.limited = true;
    const iso = text.match(/\b(20\d{2}-\d{2}-\d{2}T[\d:.]+Z?)\b/);
    const epoch = text.match(/resets?[^0-9]{0,20}(\d{10,13})\b/i);
    if (iso) result.resets_at = iso[1];
    else if (epoch) {
      const n = Number(epoch[1]);
      result.resets_at = new Date(n < 1e12 ? n * 1000 : n).toISOString();
    }
  }
  return result;
}

function flag(name, fallback = undefined) {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

/** Turn allowance for a task class, falling back to the global default. */
function allowanceFor(config, taskClass) {
  const classes = config.admission.task_classes ?? {};
  return classes[taskClass]?.max_turns ?? config.admission.max_turns;
}

/** Deadline for a task class, falling back to the global default. */
function deadlineFor(config, taskClass) {
  const classes = config.admission.task_classes ?? {};
  return classes[taskClass]?.deadline_minutes ?? config.admission.deadline_minutes;
}

const commands = {
  status(config) {
    let state = readState(config.state_branch);
    state = pruneRuns(state, config.governor.ledger_retention_days);
    const { state: pruned, expired } = pruneInFlight(state);
    const decision = decide({ config, state: pruned, queueDepth: Number(flag("queue-depth", "1")) });
    console.log(JSON.stringify({ decision, in_flight: pruned.in_flight, expired, limit: pruned.limit }, null, 2));
  },

  claim(config) {
    const issue = Number(flag("issue"));
    const runId = flag("run-id");
    const taskClass = flag("task-class", "standard");
    // The class's own deadline is the fallback, not the global default: a
    // `mechanical` claim held a 90-minute slot under the global default, so a
    // dead 30-minute task blocked the WIP limit for an extra hour.
    const minutes = Number(flag("deadline-minutes", String(deadlineFor(config, taskClass))));
    updateState(
      config.state_branch,
      (state) => {
        const { state: pruned } = pruneInFlight(state);
        if (pruned.in_flight.some((entry) => entry.issue === issue)) {
          throw new Error(`issue #${issue} is already in flight`);
        }
        if (pruned.in_flight.length >= config.admission.wip_limit) {
          throw new Error(`WIP limit ${config.admission.wip_limit} reached; not claiming #${issue}`);
        }
        pruned.in_flight.push({
          issue,
          run_id: runId,
          task_class: taskClass,
          started_at: new Date().toISOString(),
          deadline_at: new Date(Date.now() + minutes * 60000).toISOString(),
        });
        return pruned;
      },
      { message: `factory: claim #${issue}` },
    );
    console.log(`claimed #${issue} (${taskClass}, deadline ${minutes}m)`);
  },

  record(config) {
    const issue = Number(flag("issue"));
    const runId = flag("run-id");
    const outcome = flag("outcome", "failed");
    const executionFile = flag("execution-file");
    const raw = executionFile && existsSync(executionFile) ? readFileSync(executionFile, "utf8") : null;
    const parsed = parseExecution(raw);
    const explicitTurns = flag("turns");

    updateState(
      config.state_branch,
      (state) => {
        const entry = (state.in_flight ?? []).find((item) => item.issue === issue);
        const taskClass = entry?.task_class ?? "standard";
        const turns = explicitTurns !== undefined
          ? Number(explicitTurns)
          : parsed.turns ?? allowanceFor(config, taskClass);

        state.in_flight = (state.in_flight ?? []).filter((item) => item.issue !== issue);
        state.runs = state.runs ?? [];
        state.runs.push({
          issue,
          run_id: runId,
          task_class: taskClass,
          outcome,
          turns,
          turns_estimated: explicitTurns === undefined && parsed.turns === null,
          cost_usd: parsed.cost_usd,
          started_at: entry?.started_at ?? new Date().toISOString(),
          finished_at: new Date().toISOString(),
        });

        if (parsed.limited || outcome === "limited") {
          recordLimit(state, {
            resetsAt: parsed.resets_at,
            source: `issue #${issue} run ${runId}`,
            cooldownMinutes: config.governor.default_cooldown_minutes,
          });
        }
        return pruneRuns(state, config.governor.ledger_retention_days);
      },
      { message: `factory: record #${issue} ${outcome}` },
    );
    console.log(`recorded #${issue} as ${outcome}${parsed.limited ? " (usage limit observed — admission held)" : ""}`);
  },

  release(config) {
    const issue = Number(flag("issue"));
    updateState(
      config.state_branch,
      (state) => {
        state.in_flight = (state.in_flight ?? []).filter((item) => item.issue !== issue);
        return state;
      },
      { message: `factory: release #${issue}` },
    );
    console.log(`released #${issue}`);
  },

  pause(config) {
    const reason = flag("reason", "paused by operator");
    updateState(config.state_branch, (state) => ({ ...state, paused: true, paused_reason: reason }), {
      message: "factory: pause",
    });
    console.log(`paused: ${reason}`);
  },

  resume(config) {
    updateState(config.state_branch, (state) => ({ ...state, paused: false, paused_reason: null }), {
      message: "factory: resume",
    });
    console.log("resumed");
  },
};

/** Assertions over the execution-log parser. No repo, no network, no branch. */
async function selfTest() {
  const assert = await import("node:assert/strict");

  assert.deepEqual(parseExecution(null), { turns: null, cost_usd: null, limited: false, resets_at: null },
    "a missing execution file degrades to nulls rather than throwing");
  assert.deepEqual(parseExecution("not json at all"), { turns: null, cost_usd: null, limited: false, resets_at: null },
    "an unparseable execution file degrades rather than throwing");

  const nested = JSON.stringify({ result: { num_turns: 7, total_cost_usd: 1.25 } });
  assert.equal(parseExecution(nested).turns, 7, "turns are found at any depth");
  assert.equal(parseExecution(nested).cost_usd, 1.25, "cost is found at any depth");

  const limited = JSON.stringify({ error: "Claude usage limit reached, resets at 2026-09-14T18:00:00Z" });
  assert.equal(parseExecution(limited).limited, true, "a usage-limit message is detected");
  assert.equal(parseExecution(limited).resets_at, "2026-09-14T18:00:00Z", "an ISO reset time is extracted");

  const epoch = JSON.stringify({ error: "usage limit reached; resets 1789329600" });
  assert.equal(parseExecution(epoch).resets_at, new Date(1789329600 * 1000).toISOString(),
    "a unix reset timestamp is normalised to ISO");

  const vague = JSON.stringify({ error: "429 Too Many Requests" });
  assert.equal(parseExecution(vague).limited, true, "a bare 429 still counts as limited");
  assert.equal(parseExecution(vague).resets_at, null,
    "no reset time is invented when none was given — the caller falls back to the configured cooldown");

  console.log("factory CLI self-test: all assertions passed");
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const command = process.argv[2];
  if (command === "--self-test") {
    selfTest().catch((error) => {
      console.error(error);
      process.exit(1);
    });
  } else if (!commands[command]) {
    console.error(`usage: factory.mjs <${Object.keys(commands).join("|")}|--self-test> [flags]`);
    process.exit(2);
  } else {
    try {
      commands[command](loadConfig());
    } catch (error) {
      // A refused claim (WIP full, already in flight) is an expected outcome the
      // conductor has to be able to read, not a crash — a raw stack trace here
      // buries the reason in a failed step nobody reads.
      console.error(`factory ${command}: ${error.message}`);
      process.exit(1);
    }
  }
}
