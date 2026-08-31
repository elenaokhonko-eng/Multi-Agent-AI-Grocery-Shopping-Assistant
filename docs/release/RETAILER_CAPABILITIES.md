# Retailer Capability Matrix

**Audit Baseline:** `821e3dccfce00c2405faf9aace7b2b69c373fc68`  
**Last Updated:** 2026-08-31 (Post PR-08 Release Completion)

In accordance with **AD-11 (Store Capability Gating)**, every retailer integration exposes explicit capability flags. A capability is marked `🟢 Live / Verified` only after live contract acceptance criteria have been verified with sanitized evidence from the live retailer.

---

## 1. Capability Status Matrix

| Capability | FairPrice | Sheng Siong | Little Farms | RedMart | Contract Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`search_discovery`** | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | Search top-N products via live online store API/Web |
| **`pinned_sku_lookup`** | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | Fetch live metadata and stock for pinned retailer SKU |
| **`session_auth_check`** | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | Verify live authenticated state from account page |
| **`challenge_detection`** | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | Detect OTP, CAPTCHA, login expiry without stealth bypass |
| **`cart_baseline_check`** | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | Detect pre-existing unowned cart lines (`CART_CONFLICT`) |
| **`cart_mutation`** | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | Mutate real retailer cart with exact calculated packs |
| **`cart_authoritative_read`**| 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | Extract authoritative subtotal, fees, and gross total |
| **`delivery_slots`** | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | Fetch address-specific slots and select preferred slot |
| **`exact_revalidation`** | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | 🟢 Live / Verified | Multiset comparison against approved live cart |
| **`live_checkout`** | 🔒 Guarded (Opt-In) | 🔒 Guarded (Opt-In) | 🔒 Guarded (Opt-In) | 🔒 Guarded (Opt-In) | Single-click order submission guarded by env allowlist |

---

## 2. Retailer Fee Schedules & Thresholds (Authoritative)

| Retailer | Free Delivery Threshold | Base Delivery Fee | Service Fee | Bag / Packaging Fee | Default Slot Fee |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **FairPrice** | $80.00 (8000¢) | $5.00 (500¢) | $0.60 (60¢) | $0.15 (15¢) | $0.00 / $1.00 / $2.00 |
| **Sheng Siong** | $60.00 (6000¢) | $4.00 (400¢) | $1.50 (150¢) | $0.10 (10¢) | $0.00 / $1.50 |
| **Little Farms** | $100.00 (10000¢) | $12.00 (1200¢) | $0.00 (0¢) | $0.00 (0¢) | $0.00 |
| **RedMart** | $60.00 (6000¢) | $3.99 (399¢) | $0.99 (99¢) | $0.10 (10¢) | $0.00 / $1.99 |

---

## 3. Release Gate Rules
- **No Mock Masking:** Live mode (`RETAILER_DATA_MODE=live`) fails closed with `LIVE_RUN_MOCK_BLOCKED` if live retailer connectivity or search fails and `ALLOW_MOCK_FALLBACK` is false.
- **Controlled Checkout:** `live_checkout` requires both `LIVE_PURCHASE_ENABLED=true` and explicit inclusion in `LIVE_PURCHASE_RETAILER_ALLOWLIST`. Any missing approval token, unauthenticated session, or cart drift halts checkout immediately.
