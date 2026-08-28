# ADR-002: Unified FastAPI OpenAPI Specification & SSE Event Protocol

**Status:** APPROVED & FROZEN  
**Author:** Chief Architect (`fullstack-reviewer`)  
**Scope:** `apps/api/**`, `Frontend/src/services/api.ts`

---

## 1. Context & Motivation
Previously, the backend was split between legacy Flask scripts, Node/Express prototypes, and uncoordinated routes. This ADR freezes the single unified **FastAPI** OpenAPI REST contract and the Server-Sent Events (SSE) streaming protocol.

---

## 2. REST Endpoints Specification

### 2.1 Shopping List Management

#### `GET /shopping-lists`
* **Response `200 OK`:** `List[ShoppingListRead]`

#### `POST /shopping-lists`
* **Request Body:** `ShoppingListCreate` (`name: str`, `description: Optional[str]`)
* **Response `201 Created`:** `ShoppingListRead`

#### `GET /shopping-lists/{id}`
* **Response `200 OK`:** `ShoppingListWithItemsRead` (Includes all items and active version)
* **Response `404 Not Found`**

#### `PATCH /shopping-lists/{id}`
* **Request Body:** `ShoppingListUpdate` (`name: Optional[str]`, `is_active: Optional[bool]`)
* **Response `200 OK`:** `ShoppingListRead`

#### `POST /shopping-lists/{id}/items`
* **Request Body:** `ShoppingListItemCreate`
  ```json
  {
    "name": "Meiji Fresh Milk 2L",
    "category": "Dairy",
    "desired_quantity": 2,
    "unit_measure": "L",
    "must_have": true,
    "substitution_policy": "SAME_BRAND_ONLY",
    "preferred_brands": ["Meiji"],
    "exclusions": ["Skimmed", "Soy"]
  }
  ```
* **Response `201 Created`:** `ShoppingListItemRead` (Increments list version)

#### `PATCH /shopping-lists/{id}/items/{item_id}`
* **Request Body:** `ShoppingListItemUpdate`
* **Response `200 OK`:** `ShoppingListItemRead` (Increments list version)

#### `DELETE /shopping-lists/{id}/items/{item_id}`
* **Response `204 No Content`** (Increments list version)

---

### 2.2 Comparison Runs & Orchestration

#### `POST /comparison-runs`
* **Request Body:**
  ```json
  {
    "shopping_list_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "retailer_ids": ["fairprice", "shengsiong", "littlefarms", "redmart"]
  }
  ```
* **Behavior:**
  1. Validates that the shopping list exists and contains at least 1 enabled item.
  2. Creates an immutable `ComparisonSnapshot` freezing the item list and version.
  3. Initializes a `ComparisonRun` with status `QUEUED`.
  4. Launches background concurrent retailer workers.
* **Response `202 Accepted`:**
  ```json
  {
    "run_id": "7b123456-5717-4562-b3fc-2c963f66afa6",
    "snapshot_id": "8c234567-5717-4562-b3fc-2c963f66afa6",
    "status": "QUEUED",
    "created_at": "2026-08-28T21:30:00Z"
  }
  ```

#### `GET /comparison-runs/{run_id}`
* **Response `200 OK`:** `ComparisonRunDetailsRead` (Includes per-store quote summaries, current store states, and cheapest eligible winner).

#### `GET /comparison-runs/{run_id}/events` (SSE Stream)
* **Headers:** `Content-Type: text/event-stream`, `Cache-Control: no-cache`
* **Event Stream Protocol:** (Detailed in Section 3).

---

### 2.3 Approvals & Order Submission (Strict Server-Authoritative Boundary)

#### `POST /quotes/{quote_id}/approve`
* **Request Body:**
  ```json
  {
    "delivery_slot_id": "slot_fp_20260829_morning"
  }
  ```
* **Behavior:**
  1. Loads quote from database and validates it has not expired (`expires_at > now()`).
  2. Generates single-use `approval_token`, idempotency key, and computes `expected_fingerprint`.
  3. Returns approval contract with 15-minute expiry.
* **Response `200 OK`:**
  ```json
  {
    "approval_id": "app_987654",
    "approval_token": "tok_sec_1234567890abcdef",
    "quote_id": "quote_123",
    "retailer_id": "fairprice",
    "gross_total_cents": 4250,
    "delivery_slot_id": "slot_fp_20260829_morning",
    "expires_at": "2026-08-28T21:45:00Z"
  }
  ```

#### `POST /approvals/{approval_id}/submit`
* **Request Body:**
  ```json
  {
    "approval_token": "tok_sec_1234567890abcdef"
  }
  ```
* **Strict Server Validation:**
  1. Validates token matches `approval_id`, is unused (`is_used == false`), and is not expired.
  2. Acquires single-flight lock for `approval_id`.
  3. Re-reads current live retailer cart.
  4. Compares live cart against `expected_fingerprint`.
     - If cart changed -> marks approval invalid, returns `409 Conflict` with `CartDiff` and state `REAPPROVAL_REQUIRED`.
  5. Enforces `LIVE_PURCHASE_ENABLED` flag:
     - If `false` -> executes safety stop, returns `403 Forbidden` with diagnostic "LIVE_PURCHASE_DISABLED".
     - If `true` -> clicks final order submit, captures real retailer order number.
  6. Marks `approval.is_used = true` and records `OrderReceipt`.
* **Response `200 OK`:**
  ```json
  {
    "order_id": "ord_554433",
    "retailer_order_id": "FP-20260828-998877",
    "retailer_id": "fairprice",
    "confirmed_total_cents": 4250,
    "confirmed_delivery_slot": "Saturday 29 Aug, 09:00 - 11:00",
    "status": "CONFIRMED",
    "placed_at": "2026-08-28T21:32:00Z"
  }
  ```

#### `GET /orders/{order_id}`
* **Response `200 OK`:** `OrderReceiptRead`

---

## 3. Server-Sent Events (SSE) Protocol

Streamed over `GET /comparison-runs/{run_id}/events`:

```
event: store_state
data: {"retailer_id": "fairprice", "state": "SEARCHING", "progress_pct": 30, "detail": "Searching for 5 items"}

event: store_state
data: {"retailer_id": "shengsiong", "state": "USER_ACTION_REQUIRED", "challenge_type": "CAPTCHA", "resume_token": "res_ss_8877"}

event: store_quote
data: {"retailer_id": "fairprice", "quote_id": "quote_123", "gross_total_cents": 4250, "is_complete": true, "fingerprint": "fp_abc123"}

event: run_complete
data: {"run_id": "7b123456", "status": "COMPLETED", "cheapest_complete_store": "fairprice"}
```
