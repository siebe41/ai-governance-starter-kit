# 🎨 Domain Templates (Optional Overlays)

Subfolders in this directory represent **domain-specific overlays** that engineers can select during onboarding to supplement the `global/` rules.

---

## 📁 Available Overlays

* **`UI/`**: Frontend/accessibility rules — currently the only populated overlay. See `templates/UI/readme.md`.
* `Cloud/`, `DevOps/`: Not yet populated — see below.

---

## 📁 Creating a New Domain Template

To add a new team or tech-stack overlay (e.g., `Cloud`, `UI`, `DevOps`), create a subfolder with matching asset directories:

```text
templates/YourDomainName/
├── instructions/    # Domain-specific markdown rules (e.g., Terraform or React standards)
├── prompts/         # Domain-specific prompt templates
├── agents/          # Domain-specific custom agent roles
├── skills/          # Domain-specific Claude Skills
├── overlay.json     # Optional: {"applyTo": "<glob>"} scopes these rules to matching files in Copilot
└── readme.md        # What this overlay adds and why (see templates/UI/readme.md for the pattern)
```

Only populate the subfolders you actually need — `templates/UI/` currently ships `instructions/` only. aigov skips any subfolder that doesn't exist for a selected template. Without `overlay.json`, the overlay's rules load on every Copilot request, and aigov says so after each run.

The rule of thumb for **global vs. domain**: if every project should have it regardless of stack, it belongs in `global/`. If it's only relevant to projects with a UI, a cloud deployment, or a specific pipeline, it belongs in the matching `templates/<Domain>/` — that keeps `global/instructions/` short and keeps a backend service's generated instructions free of rules (like WCAG accessibility criteria) that don't apply to it.
