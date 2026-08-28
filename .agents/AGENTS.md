# Workspace Governance & Multi-Agent Rules

All agent work in this repository must strictly adhere to the following shared rules and boundaries:

## 1. Non-Negotiable Safety & Transaction Integrity Rules
- **Base Commit:** Start work from main commit `7a6c7c3`.
- **Live Purchases:** Disabled until final architectural sign-off by `fullstack-reviewer`.
- **Credentials & Security:** Never handle, store, or log card numbers, CVVs, passwords, OTPs, or CAPTCHA data.
- **No Bypasses / Spoofing:** Never bypass retailer security controls or spoof browser headers / identity.
- **Explicit Challenges:** Challenges (Incapsula, hCaptcha, Cloudflare, login expiry) must explicitly set state to `USER_ACTION_REQUIRED` with a resume token. Never loop on CAPTCHA.
- **No Silent Mock Replacement:** Never replace failed live scraper calls with mock data. Fixtures must be explicitly labelled and restricted to test suites.
- **Deterministic Selection:** Exact pinned SKU first; apply taxonomy, category, pack, quantity, and exclusion gates. Never select first search result arbitrarily.
- **Cart Ownership:** Never clear unowned items in a retailer cart; return `CART_CONFLICT`.
- **No Filler Items:** Never add filler products to reach free delivery.
- **Post-Approval Lock:** Never substitute, add, remove, or change quantity after user approval. Any cart diff triggers `REAPPROVAL_REQUIRED`.
- **Client Boundary:** The frontend submits strictly `{"quote_id": "...", "delivery_slot_id": "..."}`. Never accept client-authoritative items, prices, or totals.
- **Verified Confirmation:** No order is considered successful without a real retailer confirmation number.
- **Directory & Branch Discipline:** Work only in assigned directories and branches. Every assignment finishes with changed files, commands run, failures, residual risks, and handoff notes.

## 2. File Ownership Boundaries
- `graph-engineer`: `apps/api/**`, `packages/domain/**`, `packages/orchestration/**`, migrations, runtime configuration.
- `scraper-specialist`: `packages/retailers/**`, `apps/browser_worker/**`, session bootstrap scripts, redacted fixtures.
- `ui-frontend-engineer`: `Frontend/src/**`, generated API client & types.
- `test-specialist`: `tests/**`, `Frontend/**/__tests__/**`, `.github/workflows/**`, `docs/qa/**`.
- `fullstack-reviewer`: `docs/adr/**`, `docs/reviews/**`, final architecture gate and PROD release authority.
