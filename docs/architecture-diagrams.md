# Enterprise AI Reference Architectures

> **Author:** Andrew J. Siebert ([@Siebe41](https://github.com/Siebe41))

This document provides visual architectural models detailing how the Gateway, Local Models, Azure OpenAI, and Model Context Protocol (MCP) servers interact in enterprise environments.

---

## 1. Unified Gateway & Dynamic Model Routing Pattern

This pattern decouples client interfaces (IDEs, CLI tools, custom web apps) from underlying model providers. The Gateway enforces token metering, secret suppression, and cost-optimized routing before any prompt hits an LLM.

```mermaid
flowchart TD
    subgraph Clients["1. Client Tier"]
        IDE["VS Code / GitHub Copilot"]
        CLI["Custom Developer CLI"]
        Web["Internal Web Applications"]
    end

    subgraph Gateway["2. Local / Enterprise Gateway"]
        direction TB
        Filter["🔒 Secret Suppressor<br/><i>Regex Key & Token Filter</i>"]
        Logger["📊 Telemetry & Metering<br/><i>User ID, Audit Logs, Token Usage</i>"]
        Router{"🔀 Dynamic Model Router<br/><i>Cost & Complexity Heuristic</i>"}
        
        Filter --> Logger --> Router
    end

    subgraph Providers["3. Execution Tier"]
        Local["🖥️ Local Engine<br/><i>Ollama / LM Studio (On-Prem)</i><br/><b>Cost: $0 / Routine Tasks</b>"]
        Azure["☁️ Azure OpenAI Service<br/><i>Private Tenant / VNet Endpoint</i><br/><b>Enterprise / Complex Reasoning</b>"]
    end

    Clients --> Filter
    Router -- "Low Complexity / Drafts" --> Local
    Router -- "High Complexity / Orchestration" --> Azure

```

---

## 2. Multi-Agent Coordinator-Worker Execution Pattern

To handle non-trivial tasks, execution is divided using a **Coordinator-Worker** pattern. Complex prompts are decomposed by a Coordinator, processed in parallel by domain-specific Workers, and verified by a Validator before committing changes.

```mermaid
flowchart TD
    User(["👤 User Request / Prompt"]) --> Coordinator

    subgraph Orchestrator["Agent Workflow Engine"]
        Coordinator["🧩 Coordinator Agent<br/><i>Task Decomposition & Context Indexing</i>"]
        
        subgraph Workers["Parallel Workers"]
            Researcher["🔍 Researcher Agent<br/><i>Context Gathering</i>"]
            Implementer["💻 Implementer Agent<br/><i>Code & Spec Drafts</i>"]
        end

        Validator["🛡️ Validator Agent<br/><i>Policy, Safety & Compliance Check</i>"]
    end

    Coordinator -->|Sub-task 1| Researcher
    Coordinator -->|Sub-task 2| Implementer
    
    Researcher -->|Artifacts| Validator
    Implementer -->|Code Draft| Validator

    Validator -->|Passed| Output(["✅ Approved Execution Output"])
    Validator -.->|Rejected / Revision Needed| Coordinator

```

---

## 3. Secure Tooling Integration via Model Context Protocol (MCP)

Model Context Protocol (MCP) isolates model reasoning engines from direct database or API access. Agents request structured tool calls, and the MCP server enforces identity boundaries, permission scopes, and rate limits.

```mermaid
flowchart LR
    subgraph AgentEngine["Agent Reasoning Environment"]
        Agent["🤖 AI Agent"]
        LLM["🧠 Model Engine<br/><i>(Azure OpenAI / Local)</i>"]
        Agent <-->|Prompts & Inference| LLM
    end

    subgraph MCPLayer["Enterprise Governance Layer"]
        MCPServer["🔌 Enterprise MCP Server<br/><i>Access Control & Schema Enforcer</i>"]
    end

    subgraph Infrastructure["Enterprise Systems"]
        DevOps["📋 Azure DevOps / Jira API"]
        GitWorktree["🌲 Isolated Git Worktrees"]
        InternalDB["🔒 Internal Read-Only Context"]
    end

    Agent <-->|"Standard JSON-RPC (MCP Protocol)"| MCPServer
    MCPServer <-->|"Scoped API Calls"| DevOps
    MCPServer <-->|"File Operations"| GitWorktree
    MCPServer <-->|"Indexed Queries"| InternalDB

```

---

## 4. Sub-Repository / Submodule Integration Flow

How the starter kit embeds inside existing enterprise source trees without coupling parent project code to specific model providers.

```mermaid
flowchart TD
    subgraph ParentRepo["Parent Enterprise Repository"]
        AppCode["/src (Application Business Logic)"]
        ParentEnv[".env (Parent Config & Keys)"]
        
        subgraph Submodule["/vendor/ai-governance (This Starter Kit)"]
            SubGateway["/gateway (FastAPI Proxy)"]
            SubMCP["/mcp_servers (Tool Adapters)"]
            SubDocs["/docs (Playbook & Diagrams)"]
        end
    end

    ParentEnv -.->|Loads Config| SubGateway
    AppCode -->|Routes AI Calls| SubGateway
    SubGateway -->|Executes Tools| SubMCP

```

```

```
