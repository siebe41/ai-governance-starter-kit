# 🎨 Domain Templates (Optional Overlays)

Subfolders in this directory represent **domain-specific overlays** that engineers can select during onboarding to supplement the `global/` rules.

---

## 📁 Creating a New Domain Template

To add a new team or tech-stack overlay (e.g., `Cloud`, `UI`, `DevOps`), create a subfolder with matching asset directories:

```text
templates/YourDomainName/
├── instructions/    # Domain-specific markdown rules (e.g., Terraform or React standards)
├── prompts/         # Domain-specific prompt templates
└── agents/          # Domain-specific custom agent roles