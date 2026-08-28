# ADR-005: Multi-Agent Workstream Governance, File Boundaries & Staged Handoffs

**Status:** APPROVED & FROZEN  
**Author:** Chief Architect (`fullstack-reviewer`)  
**Scope:** Repository-wide Workstream Coordination & Release Management

---

## 1. Context & Motivation
To prevent multi-agent race conditions, uncoordinated file edits, and architectural drift, this ADR formally freezes workstream boundaries, branch conventions, and the staged handoff pipeline.

---

## 2. Workstream Matrix

| Role | Branch | Directory Ownership | Mandatory Hand-off Artifact |
| :--- | :--- | :--- | :--- |
| **`fullstack-reviewer`** | `review/production-readiness` | `docs/adr/**`, `docs/reviews/**` | ADR Contract Freeze (Step 1) & Final PROD Decision (Step 7) |
| **`graph-engineer`** | `refactor/domain-orchestration-foundation` | `apps/api/**`, `packages/domain/**`, `packages/orchestration/**`, migrations | Runnable Backend, Migrations & OpenAPI Spec |
| **`scraper-specialist`** | `feat/live-retailer-adapters` | `packages/retailers/**`, `apps/browser_worker/**` | 4 Retailer Adapters + Session Bootstrap Scripts |
| **`ui-frontend-engineer`** | `feat/canonical-shopping-dashboard` | `Frontend/src/**` | Canonical SPA Dashboard + SSE Live Visualizer |
| **`test-specialist`** | `test/full-workflow-readiness` | `tests/**`, `Frontend/**/__tests__/**`, `.github/workflows/**`, `docs/qa/**` | PyTest Suite, CI Workflow & Master QA Readiness Report |

---

## 3. Staged Handoff Protocol

```
Step 1: Contract Freeze (Current Stage - APPROVED by fullstack-reviewer)
  └── ADR-001 through ADR-005 frozen in docs/adr/
  
Step 2: Foundation & Backend Repair (Assigned to graph-engineer)
  ├── Implement GE-01 through GE-08
  └── Handoff: Working PostgreSQL backend, FastAPI OpenAPI spec, state machine
  
Step 3: Foundation Architecture Review (Assigned to fullstack-reviewer)
  └── Sign-off on GE backend before parallel agents begin
  
Step 4: Parallel Implementation Phase
  ├── scraper-specialist (SS-01..08) builds 4 store adapters against ADR-003
  ├── ui-frontend-engineer (UI-01..10) builds SPA dashboard against ADR-002
  └── test-specialist (QA-01..05) builds CI, unit & contract tests against ADR-001..04
  
Step 5: Master Integration & Orchestration (Assigned to graph-engineer)
  └── Wire live adapters and frontend events into central state machine
  
Step 6: Master QA Verification (Assigned to test-specialist)
  ├── Execute full fixture E2E workflow (QA-06)
  └── Submit QA Execution & Readiness Report (QA-08)
  
Step 7: Final Architecture, Security & PROD Release Sign-off (Assigned to fullstack-reviewer)
  ├── Security audit & CI verification
  └── Issue formal PROD Release Decision (AR-07)
```

---

## 4. Workstream Rules of Engagement
1. **Zero Cross-Directory Writes:** No agent may write outside its owned directory tree.
2. **Contract Changes Require ADR Amendment:** If an implementation requires changing a schema or API endpoint, the agent must submit an ADR proposal to `fullstack-reviewer`.
3. **No Unsanitized Artifacts:** All test fixtures and logs must be sanitized of real personal addresses, cards, passwords, or session cookies.
