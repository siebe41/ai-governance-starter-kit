/**
 * Host capacity preflight: is this machine healthy enough to take another run?
 *
 * ## Why the WIP limit is not enough
 *
 * `wip_limit` counts *factory* work. A self-hosted runner shares its box with
 * everything else on it — CI jobs, a Docker swarm, databases, whatever else the
 * machine is for — and the factory has no visibility into any of that. Two
 * factory workers under a WIP limit of two will happily start on a host already
 * at load 30 because of a CI storm, and the thing that suffers is not the
 * factory: it is the interactive work and the pull-request checks queued behind
 * it.
 *
 * So capacity is asked of the *host*, not of the ledger, and it is asked twice:
 * by the conductor before dispatching (cheap, avoids pointless churn) and by the
 * worker before starting (authoritative, because minutes may have passed and
 * another runner on the same box may have claimed the headroom in between).
 *
 * ## Deferral is not failure
 *
 * A worker that finds the host busy **releases its claim and exits cleanly**.
 * The issue goes back to the queue with nothing consumed and nothing escalated.
 * Treating a busy host as a failed run would burn the issue's budget, label it
 * escalated, and demand a human look at a machine that was merely busy.
 *
 * Linux-only by design (`/proc`). Anywhere else it reports "ok" rather than
 * guessing — a check that cannot see the host must not block work on a host it
 * knows nothing about. It is a guard, not a gate.
 */

import { existsSync, readFileSync, statfsSync } from "node:fs";
import os from "node:os";

/** Pure evaluation, so every threshold is testable without a loaded machine. */
export function evaluate({ loadPerCpu, freeMemoryMb, freeDiskGb, limits }) {
  const reasons = [];

  if (loadPerCpu !== null && loadPerCpu > limits.max_load_per_cpu) {
    reasons.push(
      `load ${loadPerCpu.toFixed(2)}/cpu exceeds ${limits.max_load_per_cpu}`,
    );
  }
  if (freeMemoryMb !== null && freeMemoryMb < limits.min_free_memory_mb) {
    reasons.push(
      `${Math.round(freeMemoryMb)}MB available memory is under ${limits.min_free_memory_mb}MB`,
    );
  }
  if (freeDiskGb !== null && freeDiskGb < limits.min_free_disk_gb) {
    reasons.push(
      `${freeDiskGb.toFixed(1)}GB free disk is under ${limits.min_free_disk_gb}GB`,
    );
  }

  return reasons.length === 0
    ? { ok: true, reason: "host has capacity" }
    : { ok: false, reason: reasons.join("; ") };
}

/**
 * Reads the host's current state. Every probe is independently optional: a
 * value that cannot be read comes back `null` and `evaluate` skips that check
 * rather than treating "unknown" as "unhealthy".
 */
export function probe(workspace = process.cwd()) {
  const cpus = os.cpus()?.length || 1;

  let loadPerCpu = null;
  // os.loadavg() returns [0,0,0] on platforms with no load concept, which would
  // read as a perfectly idle machine — so this is sourced from /proc directly
  // and stays null anywhere that file is absent.
  if (existsSync("/proc/loadavg")) {
    const one = Number(readFileSync("/proc/loadavg", "utf8").split(/\s+/)[0]);
    if (Number.isFinite(one)) loadPerCpu = one / cpus;
  }

  let freeMemoryMb = null;
  if (existsSync("/proc/meminfo")) {
    const meminfo = readFileSync("/proc/meminfo", "utf8");
    // MemAvailable, not MemFree: page cache is reclaimable, and MemFree on a
    // healthy Linux box is near zero by design. Using MemFree here would defer
    // every single run forever.
    const match = meminfo.match(/^MemAvailable:\s+(\d+) kB/m);
    if (match) freeMemoryMb = Number(match[1]) / 1024;
  }

  let freeDiskGb = null;
  try {
    const stats = statfsSync(workspace);
    freeDiskGb = Number(stats.bavail * stats.bsize) / 1024 ** 3;
  } catch {
    /* unsupported platform or unreadable mount — stays null */
  }

  return { cpus, loadPerCpu, freeMemoryMb, freeDiskGb };
}

export function checkHost(config, workspace = process.cwd()) {
  const limits = config.host ?? {};
  if (limits.enabled === false) return { ok: true, reason: "host checks disabled", probe: null };
  const reading = probe(workspace);
  return { ...evaluate({ ...reading, limits }), probe: reading };
}

async function selfTest() {
  const assert = await import("node:assert/strict");
  const limits = { max_load_per_cpu: 0.7, min_free_memory_mb: 2048, min_free_disk_gb: 10 };
  const healthy = { loadPerCpu: 0.2, freeMemoryMb: 8000, freeDiskGb: 100, limits };

  assert.equal(evaluate(healthy).ok, true, "an idle host has capacity");
  assert.equal(evaluate({ ...healthy, loadPerCpu: 3.0 }).ok, false, "a loaded host is deferred");
  assert.equal(evaluate({ ...healthy, freeMemoryMb: 500 }).ok, false, "low memory defers");
  assert.equal(evaluate({ ...healthy, freeDiskGb: 2 }).ok, false, "low disk defers");

  // Unknown must never read as unhealthy — a probe that cannot see the host
  // must not block work on a host it knows nothing about.
  assert.equal(
    evaluate({ loadPerCpu: null, freeMemoryMb: null, freeDiskGb: null, limits }).ok,
    true,
    "unreadable probes do not block admission",
  );

  // Exactly at the threshold is allowed; the comparison is strict on purpose so
  // a limit of 0.7 does not defer a host sitting at exactly 0.7.
  assert.equal(evaluate({ ...healthy, loadPerCpu: 0.7 }).ok, true, "at the load limit is still ok");
  assert.equal(evaluate({ ...healthy, freeMemoryMb: 2048 }).ok, true, "at the memory limit is still ok");

  const multi = evaluate({ ...healthy, loadPerCpu: 3.0, freeMemoryMb: 100 });
  assert.match(multi.reason, /load .*; .*memory/, "every failing check is reported, not just the first");

  const real = probe();
  assert.ok(real.cpus >= 1, "cpu count is readable");
  console.log("hostcheck self-test: all assertions passed");
  console.log("this host right now:", JSON.stringify(real));
}

if (import.meta.url === `file://${process.argv[1]}`) {
  if (process.argv.includes("--self-test")) {
    selfTest().catch((error) => {
      console.error(error);
      process.exit(1);
    });
  } else {
    const { loadConfig } = await import("./ledger.mjs");
    const result = checkHost(loadConfig());
    console.log(JSON.stringify(result, null, 2));
    if (process.env.GITHUB_OUTPUT) {
      const { appendFileSync } = await import("node:fs");
      appendFileSync(process.env.GITHUB_OUTPUT, `ok=${result.ok}\nreason=${result.reason}\n`);
    }
    // Never a non-zero exit: a busy host is a deferral the caller decides how to
    // handle, not an error that should fail a job.
  }
}
