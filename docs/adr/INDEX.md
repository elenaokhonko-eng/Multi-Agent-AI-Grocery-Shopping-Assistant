# Architecture Decision Records (ADR) Index

**Project:** Multi-Agent AI Grocery Shopping Assistant  
**Status:** FROZEN & APPROVED (Step 1 Contract Gate - Assignment AR-01)  
**Author:** Chief Architect (`fullstack-reviewer`)  
**Base Commit:** `7a6c7c3`

---

## 🏛️ Approved Architecture Decision Records

| ADR ID | Title | Status | Scope |
| :--- | :--- | :--- | :--- |
| [**ADR-001**](file:///c:/Users/dance/OneDrive/Documents/Grocery%20Shopping%20Assistant/Multi-Agent-AI-Grocery-Shopping-Assistant/docs/adr/ADR-001-canonical-domain-and-persistence.md) | Canonical Domain Models & PostgreSQL Persistence Strategy | `APPROVED / FROZEN` | `packages/domain/**`, Database |
| [**ADR-002**](file:///c:/Users/dance/OneDrive/Documents/Grocery%20Shopping%20Assistant/Multi-Agent-AI-Grocery-Shopping-Assistant/docs/adr/ADR-002-openapi-and-event-streaming-contract.md) | Unified FastAPI OpenAPI Specification & SSE Event Protocol | `APPROVED / FROZEN` | `apps/api/**`, `Frontend/src/**` |
| [**ADR-003**](file:///c:/Users/dance/OneDrive/Documents/Grocery%20Shopping%20Assistant/Multi-Agent-AI-Grocery-Shopping-Assistant/docs/adr/ADR-003-retailer-adapter-and-state-machine-contract.md) | Retailer Adapter Interface, State Machine & Error Taxonomy | `APPROVED / FROZEN` | `packages/retailers/**`, `packages/orchestration/**` |
| [**ADR-004**](file:///c:/Users/dance/OneDrive/Documents/Grocery%20Shopping%20Assistant/Multi-Agent-AI-Grocery-Shopping-Assistant/docs/adr/ADR-004-transaction-integrity-and-approval-gate.md) | Transaction Integrity, Quote Fingerprint & Single-Use Approval Gate | `APPROVED / FROZEN` | Security, Cart Revalidation, Submission |
| [**ADR-005**](file:///c:/Users/dance/OneDrive/Documents/Grocery%20Shopping%20Assistant/Multi-Agent-AI-Grocery-Shopping-Assistant/docs/adr/ADR-005-workstream-governance-and-handoffs.md) | Multi-Agent Workstream Governance, File Boundaries & Staged Handoffs | `APPROVED / FROZEN` | Workflow Governance & Release Protocol |

---

## 🔒 Sign-off Summary for Step 1
All five core architecture contracts have been formally drafted, validated, and frozen.
No agent is permitted to deviate from these schemas or contracts without a written proposal and sign-off by `fullstack-reviewer`.

**Next Staged Action:**
`graph-engineer` is authorized to commence work on branch `refactor/domain-orchestration-foundation` to implement **GE-01 through GE-08** against these frozen specifications.
