# Multi-Agent Grocery Assistant — Failed Release Remediation Plan

**Audience:** IDE coding agent and the five specialist agents  
**Architecture Authority:** Principal Engineer / Chief Architect  
**Previous Audited Release:** `821e3dccfce00c2405faf9aace7b2b69c373fc68`  
**Failed Release Under Review:** `73d5531eb2c960f8888edc09a9f9efbc257bd42e` (reconciled at `e11560b00e78e35528bd7ea3ba5c2c72b6308b37`)  
**Audit Date:** 2026-08-31  
**Repository:** `elenaokhonko-eng/Multi-Agent-AI-Grocery-Shopping-Assistant`  
**Working Branch:** `fix/failed-release-remediation`  
**Release Decision:** **NO-GO. Do not deploy and do not enable live purchasing.**

---

## 1. Master Instruction for Coding Agents

1. Work strictly from branch `fix/failed-release-remediation` (or `main` upon review and merge).
2. Never fabricate a retailer SKU, price, cart ID, fee, threshold, delivery slot, order number, receipt URL, authentication state, or live-capability claim.
3. Never present fixture results as live.
4. Never bypass CAPTCHA, OTP, rate limits, WAF, or human verification; do not use stealth plugins or user-agent spoofing. Challenges must become `USER_ACTION_REQUIRED`.
5. Keep `LIVE_PURCHASE_ENABLED=false`. An order is successful only after the real retailer site returns an authoritative order number or receipt. Any difference in SKU, quantity, stock, substitution, price, promotion, fee, slot, or total invalidates approval and requires a new quote and explicit re-approval.
6. Execute the plan strictly in the prescribed order (PR-R0 through PR-R9).

---

## 2. Executive Diagnosis & Outstanding Issues by Severity

### P0 — Stop-Ship and Safety Issues
- **P0-01 (Fabricated Order Confirmations):** Adapters must unconditionally raise `NotImplementedError` in `submit_order()` until a verified browser checkout engine is completed. API returns 503 `LIVE_CHECKOUT_NOT_IMPLEMENTED`.
- **P0-02 (Database Schema Recovery):** Do not rewrite applied migrations `0001` or `0002`. Create additive migration `0003_release_schema_alignment.py` adding missing columns (`source_mode`, `currency`, `eligible_subtotal_for_free_delivery_cents`, completeness counters) and foreign keys (`shopping_list_item_id`). Verify fresh and upgraded database parity.
- **P0-03 (Browser Worker Executable):** Create `apps/browser_worker/main.py`, `browser_session.py`, `context_registry.py`, and `worker_loop.py` to provide the container/process entrypoint for `compose.yaml`.
- **P0-04 (Truthful Retailer Capabilities):** Mark unverified live capabilities as `NOT_IMPLEMENTED` or `FIXTURE_ONLY` in `docs/release/RETAILER_CAPABILITIES.md`.
- **P0-05 (Durable Execution vs In-Memory Tasks):** Remove `asyncio.create_task` and generator session factories from API routes. Rely on durable task queuing with atomic row claims.
- **P0-06 (Cart Approval & Revalidation):** Fail closed on any cart difference, revalidation exception, or slot alteration.

### P1 — Workflow and Contract Correctness Gaps
- **P1-01 (Substitution Policy Enum):** Align `Frontend/src/components/ShoppingListEditor.tsx` with backend `SubstitutionPolicy` (`NO_SUBSTITUTIONS`, `SAME_BRAND_ONLY`, `SAME_CATEGORY_ANY_BRAND`, `CHEAPEST_ALTERNATIVE`).
- **P1-02 (Dashboard Hydration & Quote Lines):** Eagerly serialize `QuoteLine` in comparison run queries so item breakdowns, match status, and missing reasons render in the frontend.
- **P1-03 (Delivery Slot Selection):** Persist and return slot snapshots with quote revisions; recalculate totals upon slot selection.
- **P1-04 (Challenge / Open / Resume Routes):** Align route names and request bodies between frontend and backend (`/retailer-sessions/{id}/open` and `/comparison-runs/{run_id}/retailers/{retailer_id}/resume`). Fix `StateMachine` async transitions.
- **P1-05 (Product Matching & MatchStatus):** Persist domain-owned `MatchStatus` and scores. Validate remembered SKUs before cart addition.
- **P1-06 (Authoritative Financial Fields):** Read subtotal, discounts, fees, and gross from retailer post-slot cart.
- **P1-07 (Durable SSE Delivery):** Persist events before streaming; support `Last-Event-ID`.

### P2 — Deployment, Security, and Evidence Gaps
- **P2-01 (Deployable Compose Topology):** Ensure worker image installs Playwright, mounts profiles, runs migrations, and runs `apps.browser_worker.main`.
- **P2-02 (Secrets Scanning):** Enforce full-history secrets scanning.
- **P2-03 (Truthful Evidence Documentation):** Replace premature "production-ready" documents with SHA-pinned NO-GO evidence.
- **P2-04 (Identity & Ownership Boundary):** Enforce loopback trust and prepare user authentication boundaries.

---

## 3. Ordered Implementation Phases

- **PR-R0: Safety Rollback and Evidence Correction**
  - All 4 adapters raise `NotImplementedError` in `submit_order()`.
  - API returns 503 `LIVE_CHECKOUT_NOT_IMPLEMENTED`.
  - `RETAILER_CAPABILITIES.md`, `RELEASE_COMPLETION_EVIDENCE.md`, `QA_READINESS_REPORT.md`, `PRODUCTION_READINESS_REVIEW.md` updated to **NO-GO**.
  - Add `tests/api/test_submit_order_not_implemented.py`.

- **PR-R1: CI, Packaging, and Database Schema Recovery**
  - Add `apps/__init__.py`, `apps/api/__init__.py`, `apps/browser_worker/__init__.py`.
  - Add additive migration `packages/domain/alembic/versions/0003_release_schema_alignment.py`.
  - Update `packages/domain/alembic/env.py` to import `domain.models.core`.
  - Split `.github/workflows/ci.yml` into distinct required jobs.
  - Add migration parity test `tests/domain/test_migration_schema_alignment.py`.

- **PR-R2: API & Frontend Workflow Contracts**
  - Align substitution policy options in `Frontend/src/components/ShoppingListEditor.tsx`.
  - Eagerly serialize `QuoteLine` items in `apps/api/routers/comparison_runs.py`.
  - Align `/retailer-sessions` challenge/open/resume routes between frontend and backend.

- **PR-R3: Durable Browser Worker & Persistent Sessions**
  - Implement `apps/browser_worker/main.py`, `worker_loop.py`, `browser_session.py`.
  - Decouple API routes from in-memory tasks; make `DurableTaskQueue` claims atomic.

- **PR-R4: Product Matching, Memory & MatchStatus**
  - Persist domain `MatchStatus` (`EXACT`, `CLOSE_MATCH`, `SUBSTITUTE_SAME_BRAND`, `SUBSTITUTE_SAME_CATEGORY`, `NEEDS_REVIEW`, `NO_MATCH`).

- **PR-R5 through PR-R9: Slice Execution, Hardened Deployment & Qualification**
  - FairPrice real quote slice with purchasing disabled.
  - Fail-closed revalidation and exact diff calculation.
  - Hardened Docker/compose topology.
  - Truthful evidence and SHA-pinned release decision.

---

## 4. Test Matrix & Scenarios

- **T-01:** Add default item in frontend $\to$ persists valid `SubstitutionPolicy` enum after refresh.
- **T-02:** Comparison run polling returns full item breakdown including found and missing lines.
- **T-03:** Select slot $\to$ updates fee, total, window, revision, and fingerprint.
- **T-04:** Open/resume challenge $\to$ matching route resumes same durable task.
- **T-05 / T-06:** Fresh migration and upgrade from previous release pass ORM CRUD tests.
- **T-07:** Concurrent workers claim task $\to$ exactly one lease owner.
- **T-08:** Worker resume $\to$ sets target quantity without double packing.
- **T-09:** API restart during run $\to$ worker continues and events replay from cursor.
- **T-10 / T-11:** Live search failure fails explicitly; fixture mode clearly labeled `source_mode=FIXTURE` with approval disabled.
- **T-12 / T-13:** True multiset fingerprinting; any change triggers `REAPPROVAL_REQUIRED`.
- **T-14:** Revalidation throws / unreadable cart $\to$ fails closed with 0 checkout clicks.
- **T-15 / T-16:** Submission timeout $\to$ `SUBMISSION_UNCERTAIN`; duplicate submit $\to$ single order.
- **T-17:** Human verification $\to$ `USER_ACTION_REQUIRED` without bypass.
- **T-18:** Existing cart items $\to$ `CART_CONFLICT` without destructive clearing.
- **T-19:** Real retailer order confirmation absent $\to$ never display or persist `CONFIRMED`.
- **T-20:** Clean compose topology $\to$ DB migrates, services become healthy.

---

## 5. Resumption Checklist for the Next Session

1. Check out branch `fix/failed-release-remediation`.
2. Verify git status and review `docs/release/FAILED_RELEASE_REMEDIATION_PLAN.md`.
3. Proceed directly with **PR-R0** (adapter `NotImplementedError` rollback, 503 endpoint handling, documentation update to NO-GO, test creation) followed by **PR-R1** (additive migration 0003, packaging files, CI workflow split).
