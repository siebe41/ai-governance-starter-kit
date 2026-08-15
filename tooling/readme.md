# 🛠️ Deployment & Synchronization Tooling

This directory contains automation scripts that compile vendor-agnostic assets in `global/` and `templates/` into platform-specific configuration directories.

---

## 📄 Core Scripts

* **`sync_configs.py`**: Cross-platform Python deployment engine.
  * Combines markdown instructions into `.github/copilot-instructions.md`.
  * Copies prompts to `.vscode/prompts/`.
  * Copies agent roles to `.copilot/agents/`.
  * Formats and outputs global MCP server configs to `.vscode/mcp.json` and `.copilot/mcp.json`.
  * Seeds a `LEARNINGS.md` mistakes/gotchas log at the target repo root — only if one doesn't already exist, so accumulated entries are never overwritten by a re-sync.

---

## 🚀 Execution Options

```bash
# 1. Interactive Menu Mode (Recommended for developers)
python tooling/sync_configs.py

# 2. Automated / Headless CLI Mode (Recommended for CI/CD)
python tooling/sync_configs.py --templates Cloud DevOps --output /path/to/target-repo