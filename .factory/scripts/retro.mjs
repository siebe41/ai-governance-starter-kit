/**
 * Retro reader: what did the factory actually do, and was it worth it?
 *
 * ## It reports. It never tunes.
 *
 * Everything here is read-only and its only output is a report for a person.
 * That is a deliberate boundary, not an unfinished feature. This script has
 * exactly the information needed to argue for a bigger budget, more concurrency
 * or another audit — which is precisely why it must not be able to grant any of
 * them. A loop that can widen its own limits on its own evidence stops being
 * "unattended but bounded", and it would do it sincerely, having correctly
 * observed that it could be more useful with more room.
 *
 * So: the governor decides what may run, the retro says how that went, and a
 * human moves the numbers between the two.
 *
 * ## What it can and cannot see
 *
 * The ledger knows what the factory STARTED and what it spent. It cannot know
 * whether the work was any good — that judgement lives in whether a human
 * merged the pull request. So the workflow gathers per-issue outcomes from
 * GitHub and passes them in; `summarize` joins the two.
 *
 * An issue with no outcome data is reported as **unknown**, never folded into
 * failure. Counting silence as failure would make every report pessimistic in
 * exactly the weeks the API was flaky, and a metric that lies when
 * infrastructure hiccups is worse than no metric.
 *
 * Turn counts carry `turns_estimated` when the run's own log could not be
 * parsed. Those are surfaced as a share of the total rather than blended away:
 * if most of your accounting is estimated, the budgets rest on sand and you
 * should know that before tuning them.
 */

const DAY_MS = 24 * 60 * 60 * 1000;

function pct(part, whole) {
  return whole === 0 ? null : Math.round((part / whole) * 100);
}

function round(value, places = 2) {
  return value === null ? null : Number(value.toFixed(places));
}

/**
 * Joins ledger runs with GitHub outcomes into the numbers worth reading.
 * Pure: every input is an argument, so the whole analysis is testable without
 * a repo, a branch or a network.
 */
export function summarize({ runs = [], outcomes = {}, now = Date.now(), windowDays = 7 }) {
  const cutoff = now - windowDays * DAY_MS;
  const recent = runs.filter((run) => Date.parse(run.started_at ?? 0) >= cutoff);

  const byClass = new Map();
  const escalationsByIssue = new Map();
  let turns = 0;
  let estimatedTurns = 0;
  let cost = 0;
  let costKnown = false;
  let wastedTurns = 0; // turns spent on runs that produced nothing mergeable

  for (const run of recent) {
    const cls = run.task_class ?? "unknown";
    const bucket = byClass.get(cls) ?? { runs: 0, turns: 0, landed: 0, escalated: 0, failed: 0, merged: 0 };
    bucket.runs += 1;
    bucket.turns += Number(run.turns) || 0;

    turns += Number(run.turns) || 0;
    if (run.turns_estimated) estimatedTurns += Number(run.turns) || 0;
    if (Number.isFinite(run.cost_usd)) {
      cost += run.cost_usd;
      costKnown = true;
    }

    if (run.outcome === "landed") bucket.landed += 1;
    else if (run.outcome === "escalated") bucket.escalated += 1;
    else bucket.failed += 1;

    if (run.outcome === "escalated" || run.outcome === "failed") {
      escalationsByIssue.set(run.issue, (escalationsByIssue.get(run.issue) ?? 0) + 1);
      wastedTurns += Number(run.turns) || 0;
    }

    // "Landed" means the run opened a pull request, NOT that anyone wanted it.
    // Only a merge says the work was worth doing, so that is counted separately
    // and is the number the cost-per-outcome figure is built on.
    const outcome = outcomes[String(run.issue)];
    if (outcome?.merged) bucket.merged += 1;

    byClass.set(cls, bucket);
  }

  const merged = [...byClass.values()].reduce((n, b) => n + b.merged, 0);
  const landed = [...byClass.values()].reduce((n, b) => n + b.landed, 0);
  const escalated = [...byClass.values()].reduce((n, b) => n + b.escalated, 0);
  const failed = [...byClass.values()].reduce((n, b) => n + b.failed, 0);

  // Issues the factory touched whose fate GitHub did not tell us about.
  const unknown = recent.filter((run) => outcomes[String(run.issue)] === undefined).length;

  // An issue that escalates twice is an underspecified ISSUE, not a weak
  // worker — the single most actionable signal in the whole report, because
  // the fix is to rewrite or close it rather than to raise any budget.
  const repeatEscalations = [...escalationsByIssue.entries()]
    .filter(([, count]) => count > 1)
    .map(([issue, count]) => ({ issue, attempts: count }))
    .sort((a, b) => b.attempts - a.attempts);

  // Audit signal-to-noise: of the issues audits filed, how many did a human
  // actually act on? An audit whose issues are all closed unmerged is costing
  // budget and attention for nothing, and is the first thing to switch off.
  const auditIssues = Object.entries(outcomes).filter(([, o]) => o.from_audit);
  const auditMerged = auditIssues.filter(([, o]) => o.merged).length;
  const auditClosedUnmerged = auditIssues.filter(([, o]) => o.closed && !o.merged).length;
  const auditOpen = auditIssues.filter(([, o]) => !o.closed).length;

  return {
    windowDays,
    runs: recent.length,
    landed,
    merged,
    escalated,
    failed,
    unknown,
    turns,
    estimatedTurnShare: pct(estimatedTurns, turns),
    cost: costKnown ? round(cost) : null,
    turnsPerMerged: merged === 0 ? null : round(turns / merged, 1),
    costPerMerged: costKnown && merged > 0 ? round(cost / merged) : null,
    wastedTurnShare: pct(wastedTurns, turns),
    escalationRate: pct(escalated + failed, recent.length),
    repeatEscalations,
    byClass: [...byClass.entries()]
      .map(([name, b]) => ({
        name,
        ...b,
        turnsPerMerged: b.merged === 0 ? null : round(b.turns / b.merged, 1),
        escalationRate: pct(b.escalated + b.failed, b.runs),
      }))
      .sort((a, b) => b.turns - a.turns),
    audits: {
      filed: auditIssues.length,
      merged: auditMerged,
      closedUnmerged: auditClosedUnmerged,
      open: auditOpen,
      signalRate: pct(auditMerged, auditMerged + auditClosedUnmerged),
    },
  };
}

const n = (value, suffix = "") => (value === null || value === undefined ? "—" : `${value}${suffix}`);

export function renderMarkdown(s, { repo = "", generatedAt = new Date().toISOString() } = {}) {
  const lines = [];
  lines.push(`# Factory retro — last ${s.windowDays} days`);
  lines.push("");
  lines.push(`${repo ? `\`${repo}\` · ` : ""}generated ${generatedAt}`);
  lines.push("");

  if (s.runs === 0) {
    lines.push("No factory runs in this window. Nothing to report — which is itself fine if the queue was empty.");
    return lines.join("\n");
  }

  lines.push("## Headline");
  lines.push("");
  lines.push("| | |");
  lines.push("| :--- | ---: |");
  lines.push(`| Runs | ${s.runs} |`);
  lines.push(`| Pull requests opened | ${s.landed} |`);
  lines.push(`| **Merged by a human** | **${s.merged}** |`);
  lines.push(`| Escalated / failed | ${s.escalated} / ${s.failed} |`);
  lines.push(`| Turns spent | ${s.turns} |`);
  if (s.cost !== null) lines.push(`| Cost observed | $${s.cost} |`);
  lines.push(`| Turns per merged PR | ${n(s.turnsPerMerged)} |`);
  if (s.costPerMerged !== null) lines.push(`| Cost per merged PR | $${s.costPerMerged} |`);
  lines.push(`| Turns spent on runs that produced nothing | ${n(s.wastedTurnShare, "%")} |`);
  lines.push("");
  lines.push(
    "*Merged, not opened, is the number that matters — a pull request nobody wanted cost the same as one they did.*",
  );
  lines.push("");

  if (s.estimatedTurnShare !== null && s.estimatedTurnShare > 20) {
    lines.push(
      `> **${s.estimatedTurnShare}% of these turns are estimated, not measured.** A run whose log could not be parsed is charged its full allowance, so the real spend is lower than shown — and any budget tuned on this number is tuned on a guess. Worth fixing before acting on the figures above.`,
    );
    lines.push("");
  }
  if (s.unknown > 0) {
    lines.push(
      `> ${s.unknown} run(s) have no outcome from GitHub and are counted as **unknown**, never as failures.`,
    );
    lines.push("");
  }

  lines.push("## By task class");
  lines.push("");
  lines.push("| Class | Runs | Turns | Merged | Turns/merged | Escalation rate |");
  lines.push("| :--- | ---: | ---: | ---: | ---: | ---: |");
  for (const c of s.byClass) {
    lines.push(
      `| \`${c.name}\` | ${c.runs} | ${c.turns} | ${c.merged} | ${n(c.turnsPerMerged)} | ${n(c.escalationRate, "%")} |`,
    );
  }
  lines.push("");

  if (s.repeatEscalations.length > 0) {
    lines.push("## Issues that failed more than once");
    lines.push("");
    lines.push(
      "These are the most actionable rows in the report. A second failure on the same issue is almost never a weaker worker — it is an issue nobody has specified well enough to act on. **Rewrite it or close it; do not raise a budget at it.**",
    );
    lines.push("");
    for (const r of s.repeatEscalations) lines.push(`- #${r.issue} — ${r.attempts} attempts`);
    lines.push("");
  }

  lines.push("## Audit signal");
  lines.push("");
  if (s.audits.filed === 0) {
    lines.push("No audit-filed issues in view.");
  } else {
    lines.push(
      `${s.audits.filed} issue(s) filed by audits: **${s.audits.merged} merged**, ${s.audits.closedUnmerged} closed without merging, ${s.audits.open} still open.`,
    );
    lines.push("");
    lines.push(`Signal rate (merged ÷ decided): ${n(s.audits.signalRate, "%")}`);
    if (s.audits.signalRate !== null && s.audits.signalRate < 50 && s.audits.merged + s.audits.closedUnmerged >= 3) {
      lines.push("");
      lines.push(
        "> More than half of the decided audit issues were closed without merging. That audit is spending budget and attention to produce work you then reject — narrow its `notes`, or switch it off.",
      );
    }
  }
  lines.push("");
  lines.push("---");
  lines.push("");
  lines.push(
    "*This report changes nothing on its own. Budgets, concurrency and which audits run are all edited by a person in `.factory.json` — the factory does not tune itself, by design.*",
  );
  return lines.join("\n");
}

async function selfTest() {
  const assert = await import("node:assert/strict");
  const now = Date.parse("2026-09-14T12:00:00Z");
  const ago = (days) => new Date(now - days * DAY_MS).toISOString();

  const runs = [
    { issue: 1, task_class: "mechanical", outcome: "landed", turns: 10, cost_usd: 0.2, started_at: ago(1) },
    { issue: 2, task_class: "mechanical", outcome: "landed", turns: 12, cost_usd: 0.3, started_at: ago(2) },
    { issue: 3, task_class: "standard", outcome: "escalated", turns: 40, cost_usd: 30, started_at: ago(3), turns_estimated: true },
    { issue: 3, task_class: "standard", outcome: "escalated", turns: 40, cost_usd: 30, started_at: ago(2), turns_estimated: true },
    { issue: 9, task_class: "standard", outcome: "landed", turns: 20, cost_usd: 5, started_at: ago(30) }, // outside window
  ];
  const outcomes = {
    1: { merged: true, closed: true, from_audit: true },
    2: { merged: false, closed: true, from_audit: true },
    3: { merged: false, closed: false, from_audit: false },
  };

  const s = summarize({ runs, outcomes, now, windowDays: 7 });

  assert.equal(s.runs, 4, "runs outside the window are excluded");
  assert.equal(s.turns, 102, "turns sum only within the window");
  assert.equal(s.merged, 1, "merged counts GitHub merges, not runs that opened a PR");
  assert.equal(s.landed, 2, "landed counts runs that produced a PR");
  assert.equal(s.escalated, 2, "escalations counted");
  assert.equal(s.turnsPerMerged, 102, "turns per merged PR divides by MERGES, not runs");
  assert.equal(s.costPerMerged, 60.5, "cost per merged PR");
  assert.equal(s.estimatedTurnShare, 78, "estimated share is surfaced, not blended away");
  assert.equal(s.wastedTurnShare, 78, "turns on runs that produced nothing are reported");
  assert.equal(s.escalationRate, 50, "escalation rate over runs in window");

  assert.deepEqual(s.repeatEscalations, [{ issue: 3, attempts: 2 }], "an issue failing twice is surfaced by itself");

  assert.equal(s.audits.filed, 2, "audit-filed issues counted from outcomes");
  assert.equal(s.audits.merged, 1);
  assert.equal(s.audits.closedUnmerged, 1);
  assert.equal(s.audits.signalRate, 50, "signal rate is merged over DECIDED, ignoring still-open");

  // Unknown must never read as failure.
  const noOutcomes = summarize({ runs, outcomes: {}, now, windowDays: 7 });
  assert.equal(noOutcomes.unknown, 4, "runs with no GitHub outcome are unknown");
  assert.equal(noOutcomes.merged, 0, "unknown is not merged");
  assert.equal(noOutcomes.turnsPerMerged, null, "no merges means no ratio, not a divide-by-zero");
  assert.equal(noOutcomes.costPerMerged, null, "same for cost");

  const empty = summarize({ runs: [], outcomes: {}, now });
  assert.equal(empty.runs, 0);
  assert.match(renderMarkdown(empty), /No factory runs in this window/, "an empty window renders a real sentence");

  const md = renderMarkdown(s, { repo: "owner/repo" });
  assert.match(md, /Merged by a human/, "headline names the metric that matters");
  assert.match(md, /78% of these turns are estimated/, "the estimate warning fires above the threshold");
  assert.match(md, /#3 — 2 attempts/, "repeat failures are listed");
  assert.match(md, /does not tune itself/, "the report states its own boundary");

  console.log("retro self-test: all assertions passed");
}

if (import.meta.url === `file://${process.argv[1]}`) {
  if (process.argv.includes("--self-test")) {
    selfTest().catch((error) => {
      console.error(error);
      process.exit(1);
    });
  } else {
    const { readFileSync, existsSync, appendFileSync } = await import("node:fs");
    const { loadConfig, readState, pruneRuns } = await import("./ledger.mjs");
    const flag = (name, fallback) => {
      const i = process.argv.indexOf(`--${name}`);
      return i >= 0 ? process.argv[i + 1] : fallback;
    };
    const config = loadConfig();
    const state = pruneRuns(readState(config.state_branch), config.governor.ledger_retention_days);
    const outcomesPath = flag("outcomes");
    const outcomes = outcomesPath && existsSync(outcomesPath)
      ? JSON.parse(readFileSync(outcomesPath, "utf8"))
      : {};
    const summary = summarize({
      runs: state.runs,
      outcomes,
      windowDays: Number(flag("window-days", "7")),
    });
    const markdown = renderMarkdown(summary, { repo: process.env.GITHUB_REPOSITORY ?? "" });
    console.log(markdown);
    if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, `${markdown}\n`);
    const out = flag("out");
    if (out) (await import("node:fs")).writeFileSync(out, `${markdown}\n`);
  }
}
