---
name: factory-audit
description: Procedure for a scheduled read-only audit that files findings as GitHub issues rather than fixing them. Use when running the Factory Audit workflow, or whenever a prompt identifies you as the Factory Auditor for a dimension such as security, accessibility, SEO, dependencies, or documentation drift.
---

# Factory Audit

A recurring read-only sweep over one dimension of a repository. Your only output
is **issues**. You change no code.

That constraint is the feature. An audit that fixed what it found would be an
unsupervised refactor along an axis nobody asked about this week. An audit that
files issues puts every finding through the same admission control, budget and
human review as any other work — and lets someone read the finding before a line
changes.

## The bar a finding has to clear

Before you file anything, it must have:

- **A location.** A file path and a line or symbol. If you cannot point at the
  code, you do not have a finding.
- **A consequence.** What actually goes wrong, for whom, under what conditions.
  "This could be improved" is not a consequence. "A screen-reader user cannot
  reach the submit button because the dialog never moves focus into itself" is.
- **A fix that fits.** A concrete suggestion, sized so a worker run could do it.
  If the honest fix is a re-architecture, file it as a discussion rather than
  queue work, and say so in the body.

Anything that fails one of these three is not a finding. Drop it. The failure
mode of this feature is not missing a problem — it is filing thirty speculative
ones, at which point a human turns the whole thing off and you lose the twenty-
ninth that was real.

## Read the repo's own memory first

Before looking at a single file, read `AGENTS.md` (or `CLAUDE.md`) and `LEARNINGS.md` if the repo
has them, and the `NOTES` line in your prompt if one is set.

This is not politeness — it is the difference between a useful audit and one
that gets switched off. A mature repo has usually already *decided* things an
audit would otherwise "find":

- **Drift that is known and accepted.** A repo may state outright that certain
  docs have drifted and that the code is the source of truth. Re-reporting that
  every cycle is noise, and it buries the one genuinely new thing you found.
- **A constraint that looks like a defect.** A pinned-below-recommended value, a
  dependency held back, a rule that reads as wrong until you see the incident
  that produced it. If the repo explains why, it is not a finding.
- **A deliberate omission.** Something absent on purpose, recorded as such.

If your finding contradicts a written decision, that can still be worth filing —
but file it as *"this decision may no longer hold, and here is what changed"*,
naming the decision. That is a different and much more useful issue than
reporting the decision as a fresh discovery.

## Before filing

**Search the open issues first**, including closed ones from the last few months.
Re-filing something already queued spends the budget on work that is already
scheduled, and re-filing something deliberately closed is worse — it argues with a
decision someone already made. If a closed issue covers your finding and you
believe the decision was wrong, say that in a comment on the existing issue
rather than opening a new one.

## Filing

Respect **MAX ISSUES**. If you found more than that, file the most serious ones
and list what you left in the last issue's body so the next cycle can pick it up.

Each issue should carry:

- A title naming the specific problem, not the audit ("Dialog does not trap
  focus", not "Accessibility audit findings").
- The queue label and the audit label from your prompt, so the conductor can
  admit it and a human can tell where it came from.
- The evidence: location, consequence, suggested fix.
- Your confidence, when it is not high. An audit finding you are 60% sure of is
  still worth filing if you say it is 60%.

**If you find nothing, file nothing.** Say so in the job summary. A clean audit
is a real result, and a dimension that reports clean for a few cycles is telling
you to spend the budget elsewhere.

## The dimensions

Each of these is a starting point for the repo in front of you, not a checklist
to complete. Read what the project actually is first — an audit that doesn't know
whether the repo ships a web UI cannot do a useful accessibility pass.

**security** — Authorization gates that are conventions rather than enforced
(a route that works without the check its siblings carry). Secrets or tokens
committed, or logged. Input reaching a query, a shell, or a filesystem path
unvalidated. Dependencies with known advisories. Auth flows where the failure
mode is open rather than closed. Prefer one well-evidenced finding to five
pattern-matched ones; a false positive here costs a reviewer real time.

**accessibility** — Keyboard reachability and visible focus. Focus management on
dialogs and route changes. Labels and accessible names on controls, especially
icon-only ones. Text alternatives. Colour contrast, and colour as the only
carrier of meaning. Whether the page still works at 200% zoom and at phone width.
Target sizes on touch. Check against WCAG 2.2 AA where the repo has a stated bar.

**seo** — Only meaningful for a repo that serves public pages. Title and meta
description per route. Canonical URLs, and whether they match what is actually
served (a canonical pointing at a URL that redirects is a bug). `robots.txt` and
sitemap presence, correctness, and whether they are served from the path that
actually wins. Structured data validity. Heading structure. Whether pages meant
to be indexed are, and — just as important — whether pages not meant to be
indexed say so.

**dependencies** — Packages with published advisories. Abandoned or renamed
packages. Lockfile drift from the manifest. Duplicated major versions of one
library. Pinning that is too loose for something load-bearing, or too tight to
take a security patch. Group these: one issue per coherent upgrade, not one per
package.

**docs-drift** — Where documentation and code disagree. README setup steps that
no longer work. Documented commands that do not exist in `package.json`.
Architecture descriptions that describe a design the code has moved off. Code
comments citing files or line numbers that no longer exist. This is the cheapest
audit to run and often the highest value, because drift compounds silently and
every future agent run reads those docs as if they were true.
