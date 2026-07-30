# 🔌 Global Model Context Protocol (MCP) Configuration

This directory contains canonical runtime configurations for Model Context Protocol (MCP) servers used across the organization.

---

## 📄 Core Files

* **`mcp-servers.json`**: Standardized JSON configuration defining enterprise MCP servers (e.g., Azure DevOps, GitHub, local filesystem).

---

## 🔒 Secret & Environment Variable Ingestion

Do **not** commit hardcoded tokens or secrets into `mcp-servers.json`. Always use environment variable expansion syntax:

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-azure-devops"],
      "env": {
        "AZURE_DEVOPS_ORG_URL": "${AZURE_DEVOPS_ORG_URL}",
        "AZURE_DEVOPS_PAT": "${AZURE_DEVOPS_PAT}"
      }
    }
  }
}