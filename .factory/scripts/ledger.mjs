/**
 * Durable factory state, stored as a single `state.json` on an orphan branch.
 *
 * Why a branch and not a database: the factory has to work in any repo that
 * vendors this kit, with no infrastructure beyond the one it already has. A
 * self-hosted runner is usually ephemeral (the container is recycled per job),
 * an Actions cache is evicted without warning, and an external store is one
 * more credential to provision per repo. A branch is durable, free, already
 * authenticated by the workflow's own GITHUB_TOKEN, and gives the whole ledger
 * a git history for free — which doubles as the audit trail for what the
 * factory did while nobody was watching.
 *
 * Writes go through git plumbing (hash-object/mktree/commit-tree) rather than a
 * checkout, so the caller's working tree is never disturbed: the conductor runs
 * on the default branch and must stay there. A losing race against a concurrent
 * writer surfaces as a non-fast-forward push, which is retried against freshly
 * fetched state rather than forced — a forced push here would silently drop the
 * other writer's run record and corrupt the usage accounting the governor
 * depends on.
 *
 * No dependencies: Node 20+ stdlib only.
 */

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const KIT_DEFAULTS = path.join(HERE, "..", "factory.config.json");

const STATE_FILE = "state.json";
const EMPTY_STATE = { version: 1, runs: [], in_flight: [], limit: null, paused: false };

function git(args, options = {}) {
  return execFileSync("git", args, {
    encoding: "utf8",
    stdio: ["pipe", "pipe", "pipe"],
    ...options,
  }).trim();
}

function gitQuiet(args, options = {}) {
  try {
    return git(args, options);
  } catch {
    return null;
  }
}

/** Deep-merges a repo's `.factory.json` over the kit defaults, object keys only. */
function merge(base, override) {
  if (!isPlainObject(base) || !isPlainObject(override)) return override ?? base;
  const out = { ...base };
  for (const [key, value] of Object.entries(override)) {
    out[key] = isPlainObject(value) && isPlainObject(base[key]) ? merge(base[key], value) : value;
  }
  return out;
}

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/**
 * Resolves effective config: kit defaults, overlaid with the target repo's own
 * `.factory.json` if it has one. A repo that vendors the kit but never writes a
 * `.factory.json` gets the defaults, which ship with `enabled: false` — so
 * deploying the workflows never starts a factory nobody asked for.
 */
export function loadConfig(repoRoot = process.cwd()) {
  const defaults = JSON.parse(readFileSync(KIT_DEFAULTS, "utf8"));
  const localPath = path.join(repoRoot, ".factory.json");
  if (!existsSync(localPath)) return defaults;
  let local;
  try {
    local = JSON.parse(readFileSync(localPath, "utf8"));
  } catch (error) {
    throw new Error(`.factory.json is not valid JSON (${error.message}). Refusing to run on a half-read config.`);
  }
  return merge(defaults, local);
}

/** Reads state.json off the state branch. A branch that does not exist yet reads as empty state. */
export function readState(branch) {
  gitQuiet(["fetch", "origin", `${branch}:refs/remotes/origin/${branch}`, "--force"]);
  const raw = gitQuiet(["show", `origin/${branch}:${STATE_FILE}`]);
  if (!raw) return { ...EMPTY_STATE };
  try {
    return { ...EMPTY_STATE, ...JSON.parse(raw) };
  } catch {
    // A corrupt ledger must not wedge the factory forever, but it also must not
    // be silently replaced — the old content stays in the branch's history.
    console.error(`[ledger] ${STATE_FILE} on ${branch} is unparseable; starting from empty state.`);
    return { ...EMPTY_STATE };
  }
}

/**
 * Applies `mutate` to the current state and pushes the result. Re-reads and
 * re-applies on a non-fast-forward push, so two workers finishing at once both
 * land their run records instead of one overwriting the other.
 */
export function updateState(branch, mutate, { message = "factory: update state", attempts = 5 } = {}) {
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    const current = readState(branch);
    const next = mutate(structuredClone(current));
    const body = `${JSON.stringify(next, null, 2)}\n`;

    const blob = git(["hash-object", "-w", "--stdin"], { input: body });
    const tree = git(["mktree"], { input: `100644 blob ${blob}\t${STATE_FILE}\n` });
    const parent = gitQuiet(["rev-parse", `origin/${branch}`]);
    const commitArgs = ["commit-tree", tree, "-m", message];
    if (parent) commitArgs.push("-p", parent);
    const commit = git(commitArgs);

    try {
      git(["push", "origin", `${commit}:refs/heads/${branch}`]);
      return next;
    } catch (error) {
      if (attempt === attempts) throw error;
      console.error(`[ledger] push rejected (attempt ${attempt}/${attempts}); re-reading state and retrying.`);
    }
  }
  throw new Error("unreachable");
}

/** Drops run records past the retention window so the ledger stays a bounded file. */
export function pruneRuns(state, retentionDays) {
  const cutoff = Date.now() - retentionDays * 24 * 60 * 60 * 1000;
  state.runs = (state.runs ?? []).filter((run) => Date.parse(run.started_at ?? 0) >= cutoff);
  return state;
}

/**
 * Drops in-flight entries whose deadline has passed. A worker that is killed
 * mid-run (runner reboot, cancelled job, hard timeout) never gets to clear its
 * own entry, and without this the WIP limit would be permanently consumed by a
 * task that is not running — the factory would go quiet and look "full" forever.
 */
export function pruneInFlight(state, now = Date.now()) {
  const kept = [];
  const expired = [];
  for (const entry of state.in_flight ?? []) {
    if (Date.parse(entry.deadline_at ?? 0) > now) kept.push(entry);
    else expired.push(entry);
  }
  state.in_flight = kept;
  return { state, expired };
}

export { STATE_FILE, EMPTY_STATE };
