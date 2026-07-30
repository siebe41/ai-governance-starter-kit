# Enterprise Software Engineering Standards

---

## 📐 Architecture & Design Principles
* **Single Responsibility:** Keep functions and classes tightly scoped to a single purpose.
* **Fail Fast & Explicitly:** Handle error conditions at the boundary. Never catch and suppress exceptions silently without logging context.
* **Asynchronous Execution:** Prefer asynchronous, non-blocking I/O operations for network, disk, and database calls.

---

## 📝 Code Style & Documentation
* **Self-Documenting Code:** Write clear variable and method names that convey intent. Avoid obscure abbreviations.
* **Logging & Observability:** Include structured logs (`ILogger` / `logging`) with contextual key-value pairs (e.g., `UserId`, `OperationId`, `DurationMs`).