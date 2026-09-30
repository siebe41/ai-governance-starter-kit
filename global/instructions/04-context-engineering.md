# Context Engineering

> **Applies To:** All AI Assistants, Inline Copilots, and Agentic Workflows

Structuring code and projects so any AI coding assistant — Copilot, Claude Code, or otherwise — has enough signal to give good suggestions and make good changes.

---

## 📐 Project Structure

* **Use descriptive file paths.** `src/auth/middleware.ts` tells an assistant more than `src/utils/m.ts` — paths are part of the context, not just organization.
* **Colocate related code.** Keep components, tests, types, and hooks together so one search pattern finds everything relevant to a change.
* **Export public APIs from index files.** What's exported is the contract; what isn't is internal. This is a signal an assistant uses to infer boundaries, not just a convention for humans.

## 🧩 Code Patterns

* **Prefer explicit types over inference.** `function getUser(id: string): Promise<User>` carries more context than `function getUser(id)` — type annotations are documentation an assistant can actually use.
* **Use semantic names.** `activeAdultUsers` beats `x`. Self-documenting code is AI-readable code, not just human-readable.
* **Name constants.** `MAX_RETRY_ATTEMPTS = 3` carries intent a bare `3` doesn't.

## 💬 Working With an Assistant

* **Describe multi-file scope up front.** State every file involved before asking for a change — "update the User model, the API endpoint, and the tests" — rather than letting the assistant discover scope one file at a time.
* **Work incrementally on non-trivial changes.** One file at a time, verified, beats asking for everything at once when the change is large or unfamiliar.
* **When suggestions look stale or generic**, the fix is usually more context, not a different prompt: point at the relevant files explicitly, paste the actual code in question, name the framework and constraints, or reference an existing pattern to follow ("do it the way `src/api/users.ts` does it").

## 📄 Durable Context Hints

* Document architecture decisions, patterns, and conventions an assistant should follow in a durable file the assistant actually reads on every session (`AGENTS.md`, which GitHub Copilot and Claude Code both read; this repo's governance kit writes it).
* Use a strategic comment at the top of a genuinely complex module to state its flow or purpose in one or two lines — not to narrate what the code already makes obvious.
* Reference existing patterns explicitly rather than describing the desired result from scratch — "follow the same pattern as `src/api/users.ts`" is a concrete, checkable instruction; "make it clean and consistent" is not.
