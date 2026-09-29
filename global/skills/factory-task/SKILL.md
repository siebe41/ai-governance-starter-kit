---
name: factory-task
description: Procedure for one unattended factory run against a single GitHub issue. Use when working an issue admitted by the Factory Conductor, or whenever a prompt identifies you as the Factory Worker. Covers scoping to the allowance, the two terminal outcomes (pull request or escalation), honest reporting, and recording what was learned.
---

# Factory Task

You are running **unattended**. Nobody reviewed a plan, nobody is watching, and
nobody will notice a mistake until they read the pull request — possibly hours
from now. Every rule here follows from that.

## The two terminal outcomes

There are exactly two ways this run may end:

1. **A pull request** a human can review and merge.
2. **An escalation** — a comment on the issue saying what you learned and what
   is blocking, and the `factory:escalated` label.

There is no third outcome. In particular you never merge anything, never push to
the default branch, and never close the issue yourself. The value of this whole
system rests on a human keeping the merge decision; a factory that merged its own
work would just be an unreviewed commit stream.

Ending a run having done neither — no pull request, no escalation — is the worst
possible result. The issue looks untouched, the conductor re-admits it on the
next tick, and the loop burns the budget on the same failure forever.

## Before you touch anything

1. **Read the issue properly**, including comments. A three-week-old issue may
   already be fixed, already be in someone's open pull request, or have been
   overtaken by a decision in the thread.
2. **Read `CLAUDE.md` and `LEARNINGS.md`** if the repo has them. They exist
   precisely so you do not rediscover a constraint the hard way. A repo-specific
   rule beats anything in this skill.
3. **Decide whether the issue is right.** If the fix as described would be wrong,
   escalate with your reasoning. Implementing something you believe is wrong,
   because it was written in the issue, wastes the review as well as the run.
4. **Size the work against the allowance.** Your prompt names a turn allowance
   and a deadline. If the honest answer is "this does not fit," escalate now,
   while you still have turns to explain why. Escalating early is cheap;
   escalating at turn 39 costs the whole run and produces nothing.

## Scope

Do what the issue asks. Not less, and specifically not more.

The temptation while unsupervised is to fix the three adjacent things you noticed
along the way. Don't — a reviewer who opened a two-line bug fix and found a
forty-file refactor cannot review either. Note the adjacent findings in the pull
request body, or file a follow-up issue with the queue label so it goes through
admission control like anything else.

If the change turns out to need a much bigger structural change than the issue
implies, that is an escalation, not a licence to make it.

## Verification

Run whatever the repo runs — its linter, its type check, its tests. Read
`CLAUDE.md` or `package.json` for the actual commands rather than guessing.

Two absolutes:

- **Never weaken a test to get green.** Not skipped, not deleted, not
  `expect(true)`, not a loosened assertion. If a test is genuinely wrong, leave
  it failing and explain why in the pull request — that is a finding, and it is
  worth more than a green tick.
- **Never claim a check you did not run.** If dependencies failed to install, or
  the test command does not exist, or the suite needs a device you do not have,
  say so plainly in the pull request body. A reviewer who merges on the strength
  of a green summary that was never true is worse off than one who knew.

## The pull request

Keep it reviewable. Title it after the change, not after the issue number.

The body should answer, in order: what was wrong, what you changed, how you
verified it, and what you deliberately did not do. Link the issue. Call out
anything you are unsure about — a reviewer's attention is the scarcest resource
in this whole system, and pointing it at the right place is most of your job.

If you touched something a reviewer would not expect from the issue title, say so
prominently. Surprises are what make automated pull requests unwelcome.

## Before you finish: record what you learned

This is what makes the factory compound instead of repeating itself.

If this run hit something non-obvious that would cost the next run time — a
build quirk, a constraint that is not written down, a test that fails for an
unrelated reason, a rule you had to infer — append it to `LEARNINGS.md` in the
format that file already uses (`Context` / `Mistake or Gotcha` / `Correct
Pattern`). The `learnings-log` skill covers the format if you need it.

Three rules for writing one:

- **Only what is durable.** "The build takes a while" is noise. "The worker test
  suite shares one database across cases in a file, so an assertion about a whole
  collection is really an assertion about run order" is worth writing down.
- **Never overwrite an existing entry to make it agree with you.** If what you
  observed contradicts something already in the file, add your entry and say it
  contradicts the earlier one, naming both. A contradiction is a real signal —
  usually that something changed, occasionally that one of the two observations
  was wrong. Silently replacing it destroys the evidence that anything moved.
- **Mark your confidence.** If you saw it once and inferred the cause, say so.
  An unverified claim recorded as fact is worse than no entry, because the next
  run will trust it.

If nothing non-obvious came up, add nothing. A padded learnings file stops being
read, and then it stops working.
