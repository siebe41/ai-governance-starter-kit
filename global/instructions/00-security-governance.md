# Corporate AI Security & Governance Instructions

> **Applies To:** All AI Assistants, Inline Copilots, and Agentic Workflows  
> **Enforcement Level:** Mandatory

---

## 🔒 1. Secret & Credential Handling
* **NEVER** output or hardcode raw secrets, API keys, bearer tokens, connection strings, or private certificates in code or configuration files.
* Always use enterprise environment variables, Key Vault references, or secret managers.
* If a prompt includes a suspected raw secret, notify the user immediately and refuse execution until redacted.

---

## 🛡️ 2. Privacy & Data Handling
* Do not pass personally identifiable information (PII), end-user financial records, or non-public customer data into public AI model endpoints.
* Ensure all cloud routing targets private enterprise endpoints (e.g., Azure OpenAI Service with private endpoints).

---

## 🚧 3. Code Generation Guardrails
* **No Untrusted Dependencies:** Do not introduce third-party packages or libraries without verifying their license and security posturing.
* **Input Validation:** All generated API endpoints and input handlers must include explicit schema validation, sanitization, and boundary checks.
* **Database Queries:** Never construct raw concatenated SQL or query strings. Use parameterized queries or safe ORM mappings.