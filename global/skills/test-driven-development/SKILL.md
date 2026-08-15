---
name: test-driven-development
description: Use when writing or fixing any production code — write the failing test first, watch it fail, then write the minimal code to pass. Enforces the discipline in this repo's 02-testing-standards.md rather than just describing it.
---

# Test-Driven Development

## Core Principle

If you didn't watch the test fail, you don't know if it tests the right thing.

**The Iron Law:** No production code without a failing test first. If you wrote code before the test, delete it — don't keep it "as reference," don't "adapt" it while writing the test after the fact. Delete means delete; implement fresh from the test.

## When to Use

Always: new features, bug fixes, refactoring, behavior changes.

Exceptions (ask first, don't decide unilaterally): throwaway prototypes, generated code, configuration files. If you're thinking "skip it just this once" for anything else, that's the rationalization to catch, not a real exception.

## Red — Green — Refactor

1. **RED.** Write one minimal test for one behavior, with a name that describes that behavior. Prefer real code over mocks; a test that mocks the thing it's supposed to verify proves nothing.
2. **Verify RED (mandatory, never skip).** Run just that test. Confirm it *fails*, not errors, and fails for the reason you expect (missing feature, not a typo). A test that passes immediately is testing existing behavior — fix the test.
3. **GREEN.** Write the smallest change that makes the test pass. Don't add options, config, or generality the test didn't ask for — that's the next test's job, if there is one.
4. **Verify GREEN (mandatory).** Run the test again, then the full suite. The new test passes, nothing else broke, output is clean (no stray errors/warnings).
5. **REFACTOR.** Only after green: remove duplication, improve names, extract helpers. No new behavior here — if you need new behavior, that's a new RED.
6. Repeat for the next behavior.

## Common Rationalizations — and Why They're Wrong

| Excuse | Reality |
| :--- | :--- |
| "I'll test after" | Tests written after a pass immediately, which proves nothing — you never watched them fail, so you never proved they can catch the bug. |
| "Already manually tested it" | Manual testing leaves no record of what was covered and doesn't re-run itself when the code changes next. |
| "I've already spent hours on this, deleting is wasteful" | Sunk cost. The real choice is rewrite-with-TDD (trustworthy) vs. keep-and-bolt-tests-on (low confidence, likely bugs). |
| "This test is hard to write" | That usually means the design is hard to use, not that the test is wrong — simplify the interface. |
| "TDD will slow me down" | Debugging a regression in production is slower than writing the test first would have been. |

## Verification Checklist

Before calling the work done:
- [ ] Every new function/behavior has a test that was watched to fail first
- [ ] Each failure was for the expected reason, not a typo or setup bug
- [ ] All tests pass, full suite included, output clean
- [ ] Tests exercise real code — mocks only where a real dependency is genuinely unavailable
- [ ] Edge cases and failure paths are covered, not just the happy path

If you can't check every box, the work wasn't done test-first — go back and do it properly rather than writing tests to match code that already exists.

---
Adapted from [obra/superpowers](https://github.com/obra/superpowers/tree/main/skills/test-driven-development) (MIT License, © Jesse Vincent).
