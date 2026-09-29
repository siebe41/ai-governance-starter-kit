# Autonomous Factory Operation

> **Applies To:** Any AI run nobody is watching — scheduled jobs, queue workers, audit sweeps
> **Enforcement Level:** Mandatory where an autonomous loop is enabled

These rules are stricter than the interactive ones because the correction loop is
missing. In a chat session a person catches a wrong turn in seconds; an
unattended run's first reader is whoever opens the pull request, possibly hours
later.

---

## 🚦 1. Nothing Merges Itself

* An unattended run **may** open a pull request.
* It may **never** merge one, push to a protected or default branch, approve a review, or close an issue as done.
* The human merge decision is the only review this work receives. A system that routes around it is not a factory — it is an unreviewed commit stream.

---

## 🔚 2. Every Run Ends in a Visible Outcome

* A run ends with **a pull request** or with **an escalation** — a comment saying what was learned and what is blocking.
* Ending with neither is the worst possible result: the work looks untouched, the queue re-admits it, and the same failure repeats every cycle.
* When in doubt, escalate. A clear "here is why I stopped" is a useful result; a silent no-op never is.

---

## 💰 3. Budget Is a Boundary, Not a Target

* Unattended work draws on a shared, finite allowance — the same pool a human's interactive session uses.
* Work that does not fit its allowance is **escalated**, never half-delivered and never quietly extended.
* Decide that early, while there is still budget left to explain the decision. Escalating at the last turn costs the whole run and produces nothing.

---

## 🧾 4. Report Honestly, Especially About What You Did Not Do

* State which checks ran and which did not — a missing test suite, a failed install, a check needing hardware the runner lacks.
* **Never imply a check passed that was never run.** A reviewer who merges on the strength of a green summary that was not true is worse off than one who knew and looked harder.

---

## 🧪 5. Never Weaken a Test to Get Green

* Not skipped, not deleted, not loosened, not `expect(true)`.
* If a test is genuinely wrong, leave it failing and explain why in the pull request. A failing test that reveals a real disagreement is worth more than a green run that hid it.

---

## 🎯 6. Stay in Scope

* Do what was asked, not the three adjacent things you noticed while unsupervised.
* A reviewer who opened a small fix and found a sweeping refactor can review neither.
* Note adjacent findings in the pull request body, or file them as their own queued work so they go through the same admission and review as anything else.

---

## 🧠 7. Write Down What Would Have Saved You Time

This extends [`03-learnings-log.md`](03-learnings-log.md), which governs the
format and when to log; everything there applies. Two additions specific to
running unattended:

* **Mark your confidence.** An unattended run usually sees a thing once and infers the cause. Say so. A single-observation inference recorded as settled fact is worse than no entry at all, because the next run will trust it.
* **A contradiction is added, never overwritten.** `03` says to update an existing entry rather than duplicate it — that is about *duplicates*. When what you observed **disagrees** with an entry already there, do not edit that entry into agreement: add yours and name the contradiction, referencing both. A contradiction usually means something changed, and occasionally means one of the two observations was wrong. Either way it is a signal, and silently rewriting the old entry destroys the evidence that anything moved.
