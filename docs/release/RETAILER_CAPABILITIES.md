# Retailer Capability Matrix

**Audit Baseline:** `821e3dccfce00c2405faf9aace7b2b69c373fc68`  
**Last Updated:** 2026-08-29

In accordance with **AD-11 (Store Capability Gating)**, every retailer integration exposes explicit capability flags. A capability is marked `true` only after live contract acceptance criteria have been verified with sanitized evidence from the live retailer.

---

## 1. Capability Status Matrix

| Capability | FairPrice | Sheng Siong | Little Farms | RedMart | Contract Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`search_discovery`** | 🟡 Partial | 🟡 Partial | 🟡 Partial | 🔴 False | Search top-N products via live online store |
| **`pinned_sku_lookup`** | 🔴 False | 🔴 False | 🔴 False | 🔴 False | Fetch live metadata and stock for pinned retailer SKU |
| **`session_auth_check`** | 🔴 False | 🔴 False | 🔴 False | 🔴 False | Verify live authenticated state from account page |
| **`challenge_detection`** | 🔴 False | 🔴 False | 🔴 False | 🔴 False | Detect OTP, CAPTCHA, login expiry without bypass |
| **`cart_baseline_check`** | 🔴 False | 🔴 False | 🔴 False | 🔴 False | Detect pre-existing unowned cart lines (`CART_CONFLICT`) |
| **`cart_mutation`** | 🔴 False | 🔴 False | 🔴 False | 🔴 False | Mutate real retailer cart with exact calculated packs |
| **`cart_authoritative_read`**| 🔴 False | 🔴 False | 🔴 False | 🔴 False | Extract authoritative subtotal, fees, and gross total |
| **`delivery_slots`** | 🔴 False | 🔴 False | 🔴 False | 🔴 False | Fetch address-specific slots and select preferred slot |
| **`exact_revalidation`** | 🔴 False | 🔴 False | 🔴 False | 🔴 False | Multiset comparison against approved live cart |
| **`live_checkout`** | 🔴 False | 🔴 False | 🔴 False | 🔴 False | Single-click order submission capturing real receipt |

---

## 2. Release Gate Rule
- **No Mock Masking:** Unsupported capabilities must present an honest `UNSUPPORTED` or `USER_ACTION_REQUIRED` state in the UI. They must never return fabricated data or fall back silently to mock catalogues.
- **Controlled Checkout:** `live_checkout` remains `false` across all retailers until individual controlled-purchase acceptance gates pass in PR-07 (FairPrice) and PR-08 (remaining retailers).
