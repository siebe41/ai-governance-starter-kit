#!/usr/bin/env node
/**
 * Reads the Claude Code CLI's `--output-format json` result and emits
 * `key=value` lines for `$GITHUB_OUTPUT`.
 *
 * Why this is its own file rather than an inline `node -e` in the workflow:
 * the workflow's own shell is the wrong place to learn a data format. Here it
 * can be run against a captured result file by hand, and `--self-test` pins the
 * three shapes that matter against samples taken from a real CLI run.
 *
 * The contract, verified against claude-code 2.1.272 rather than read off a
 * doc page (the docs do not specify these keys):
 *
 *   { type: 'result', subtype: 'success', is_error: false,
 *     num_turns: 1, total_cost_usd: 0.14, terminal_reason: 'completed', ... }
 *
 * The load-bearing fact: **the CLI emits a complete result object on stdout
 * even when it exits non-zero for max turns**, with an accurate `num_turns`
 * and `total_cost_usd`. That is the whole reason the ledger can now record
 * what a failed run actually spent instead of charging it a guess.
 *
 *   max turns → exit 1, subtype 'error_max_turns', terminal_reason 'max_turns'
 *
 * Anything that is not parseable JSON means the run died before producing a
 * result at all — a different diagnosis, reported as `parsed=false` rather
 * than smoothed into a zero.
 */

import { readFileSync } from "node:fs";

export function parseCliResult(raw) {
  const out = {
    parsed: false,
    subtype: "unparseable",
    num_turns: "",
    cost_usd: "",
    is_error: "true",
    terminal_reason: "",
  };

  let d = null;
  try {
    d = JSON.parse(raw);
  } catch {
    return out;
  }
  if (!d || typeof d !== "object") return out;

  out.parsed = true;
  if (typeof d.subtype === "string") out.subtype = d.subtype;
  // A turn count of 0 is meaningful ("started, did nothing"), so test for the
  // number rather than for truthiness.
  if (Number.isFinite(d.num_turns)) out.num_turns = String(d.num_turns);
  if (Number.isFinite(d.total_cost_usd)) out.cost_usd = String(d.total_cost_usd);
  out.is_error = d.is_error === true ? "true" : "false";
  if (typeof d.terminal_reason === "string") out.terminal_reason = d.terminal_reason;
  return out;
}

export function toGithubOutput(result) {
  return Object.entries(result)
    .map(([k, v]) => `${k}=${v}`)
    .join("\n");
}

function selfTest() {
  const cases = [
    {
      name: "success",
      raw: JSON.stringify({
        type: "result",
        subtype: "success",
        is_error: false,
        num_turns: 1,
        total_cost_usd: 0.141312,
        terminal_reason: "completed",
      }),
      expect: { parsed: true, subtype: "success", num_turns: "1", is_error: "false", terminal_reason: "completed" },
    },
    {
      name: "max turns (non-zero exit, but still a full result)",
      raw: JSON.stringify({
        type: "result",
        subtype: "error_max_turns",
        is_error: true,
        num_turns: 2,
        total_cost_usd: 0.0333194,
        terminal_reason: "max_turns",
      }),
      expect: { parsed: true, subtype: "error_max_turns", num_turns: "2", cost_usd: "0.0333194", is_error: "true" },
    },
    {
      name: "died before producing a result",
      raw: "--dangerously-skip-permissions cannot be used with root/sudo privileges",
      expect: { parsed: false, subtype: "unparseable", num_turns: "", is_error: "true" },
    },
    {
      name: "empty stdout",
      raw: "",
      expect: { parsed: false, subtype: "unparseable" },
    },
  ];

  let failed = 0;
  for (const c of cases) {
    const got = parseCliResult(c.raw);
    for (const [k, want] of Object.entries(c.expect)) {
      if (String(got[k]) !== String(want)) {
        console.error(`FAIL ${c.name}: ${k} = ${got[k]!== undefined ? JSON.stringify(got[k]) : "undefined"}, want ${JSON.stringify(want)}`);
        failed += 1;
      }
    }
  }
  if (failed) {
    console.error(`${failed} assertion(s) failed`);
    process.exit(1);
  }
  console.log(`parse-cli-result: ${cases.length} cases passed`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  if (process.argv.includes("--self-test")) {
    selfTest();
  } else {
    const path = process.argv[2];
    let raw = "";
    try {
      raw = readFileSync(path, "utf8");
    } catch {
      // A missing file is the same diagnosis as unparseable output: no result.
      raw = "";
    }
    console.log(toGithubOutput(parseCliResult(raw)));
  }
}
