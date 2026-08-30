const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ShoppingListItem {
  id: string;
  name: string;
  category?: string;
  desired_quantity: number;
  unit_measure: string;
  min_pack_size?: string;
  max_pack_size?: string;
  must_have: boolean;
  is_enabled: boolean;
  substitution_policy: string;
  preferred_brands: string[];
  exclusions: string[];
  pinned_skus: Record<string, string>;
}

export interface ShoppingList {
  id: string;
  name: string;
  description?: string;
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  items_count?: number;
  items?: ShoppingListItem[];
}

export interface ComparisonRunInit {
  run_id: string;
  snapshot_id: string;
  status: string;
  target_retailers: string[];
  created_at: string;
}

export interface QuoteLineItem {
  id?: string;
  shopping_item_id: string;
  retailer_sku: string;
  product_title: string;
  product_brand?: string;
  product_url: string;
  image_url?: string;
  pack_size?: string;
  requested_quantity: number;
  packs_added: number;
  unit_price_cents: number;
  unit_measure: string;
  line_total_cents: number;
  is_in_stock: boolean;
  is_exact_match: boolean;
  is_substituted: boolean;
  missing_reason?: string;
}

export interface DeliverySlotItem {
  slot_id: string;
  start_time: string;
  end_time: string;
  fee_cents: number;
  is_available: boolean;
  display_label: string;
}

export interface StoreQuoteSummary {
  id: string;
  quote_id?: string;
  run_id: string;
  retailer_id: string;
  cart_url?: string;
  cart_fingerprint: string;
  subtotal_cents: number;
  promotions_discount_cents: number;
  delivery_fee_cents: number;
  service_fee_cents: number;
  bag_fee_cents: number;
  slot_fee_cents: number;
  gross_total_cents: number;
  derived_net_cents: number;
  gst_cents: number;
  free_delivery_threshold_cents?: number;
  amount_needed_for_free_delivery_cents: number;
  is_complete: boolean;
  is_all_items_complete: boolean;
  is_required_complete: boolean;
  requested_item_count: number;
  found_item_count: number;
  missing_item_count: number;
  missing_must_have_count: number;
  selected_delivery_slot_id?: string;
  selected_delivery_slot_window?: string;
  expires_at: string;
  lines?: QuoteLineItem[];
}

export interface StoreEventLog {
  id: string;
  run_id: string;
  retailer_id: string;
  from_state?: string;
  to_state: string;
  progress_pct: number;
  message?: string;
  action_type?: string;
  resume_token?: string;
  created_at: string;
}

export interface ComparisonRunDetails {
  id: string;
  run_id: string;
  snapshot_id: string;
  status: string;
  cheapest_complete_store?: string;
  created_at: string;
  completed_at?: string;
  quotes: StoreQuoteSummary[];
  event_logs?: StoreEventLog[];
}

export interface ApprovalResponse {
  approval_id: string;
  approval_token: string;
  quote_id: string;
  retailer_id: string;
  gross_total_cents: number;
  expected_fingerprint: string;
  delivery_slot_id: string;
  expires_at: string;
  lines?: QuoteLineItem[];
}

export interface OrderConfirmationResponse {
  status: string;
  order_id?: string;
  receipt_id: string;
  retailer_order_id: string;
  retailer_id: string;
  confirmed_total_cents: number;
  confirmed_delivery_slot: string;
  receipt_url?: string;
  placed_at: string;
}

export interface SessionStatusResponse {
  retailer_id: string;
  is_authenticated: boolean;
  user_name?: string;
  requires_action: boolean;
  action_type?: string;
  resume_token?: string;
  detail?: string;
}

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);
    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData && errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch {
        // Fallback to text message
      }
      throw new Error(errorMessage);
    }

    if (response.status === 204) {
      return null as T;
    }

    return response.json();
  }

  async getShoppingLists(): Promise<ShoppingList[]> {
    return this.request<ShoppingList[]>('/shopping-lists');
  }

  async getShoppingList(id: string): Promise<ShoppingList> {
    return this.request<ShoppingList>(`/shopping-lists/${id}`);
  }

  async createShoppingList(name: string, description?: string): Promise<ShoppingList> {
    return this.request<ShoppingList>('/shopping-lists', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
  }

  async addItem(listId: string, item: Omit<ShoppingListItem, 'id'>): Promise<ShoppingListItem> {
    return this.request<ShoppingListItem>(`/shopping-lists/${listId}/items`, {
      method: 'POST',
      body: JSON.stringify(item),
    });
  }

  async updateItem(listId: string, itemId: string, item: Partial<ShoppingListItem>): Promise<ShoppingListItem> {
    return this.request<ShoppingListItem>(`/shopping-lists/${listId}/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(item),
    });
  }

  async deleteItem(listId: string, itemId: string): Promise<void> {
    return this.request<void>(`/shopping-lists/${listId}/items/${itemId}`, {
      method: 'DELETE',
    });
  }

  async startComparison(listId: string, retailers: string[] = ['fairprice', 'shengsiong', 'littlefarms', 'redmart']): Promise<ComparisonRunInit> {
    return this.request<ComparisonRunInit>('/comparison-runs', {
      method: 'POST',
      body: JSON.stringify({
        shopping_list_id: listId,
        target_retailers: retailers,
      }),
    });
  }

  async getComparisonRun(runId: string): Promise<ComparisonRunDetails> {
    return this.request<ComparisonRunDetails>(`/comparison-runs/${runId}`);
  }

  async getQuote(quoteId: string): Promise<StoreQuoteSummary> {
    return this.request<StoreQuoteSummary>(`/quotes/${quoteId}`);
  }

  async selectQuoteSlot(quoteId: string, slotId: string): Promise<StoreQuoteSummary> {
    return this.request<StoreQuoteSummary>(`/quotes/${quoteId}/select-slot`, {
      method: 'POST',
      body: JSON.stringify({ slot_id: slotId }),
    });
  }

  async approveQuote(quoteId: string, deliverySlotId: string, idempotencyKey?: string): Promise<ApprovalResponse> {
    return this.request<ApprovalResponse>(`/quotes/${quoteId}/approve`, {
      method: 'POST',
      body: JSON.stringify({
        delivery_slot_id: deliverySlotId,
        idempotency_key: idempotencyKey,
      }),
    });
  }

  async createApproval(quoteId: string, deliverySlotId: string, idempotencyKey?: string): Promise<ApprovalResponse> {
    return this.request<ApprovalResponse>('/approvals', {
      method: 'POST',
      body: JSON.stringify({
        quote_id: quoteId,
        delivery_slot_id: deliverySlotId,
        idempotency_key: idempotencyKey,
      }),
    });
  }

  async getApproval(approvalId: string): Promise<ApprovalResponse> {
    return this.request<ApprovalResponse>(`/approvals/${approvalId}`);
  }

  async submitApproval(approvalId: string, approvalToken: string): Promise<OrderConfirmationResponse> {
    return this.request<OrderConfirmationResponse>(`/approvals/${approvalId}/submit`, {
      method: 'POST',
      body: JSON.stringify({
        approval_token: approvalToken,
      }),
    });
  }

  async checkRetailerSession(retailerId: string): Promise<SessionStatusResponse> {
    return this.request<SessionStatusResponse>(`/retailer-sessions/${retailerId}/status`);
  }

  async launchRetailerSession(retailerId: string): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>(`/retailer-sessions/${retailerId}/headed`, {
      method: 'POST',
    });
  }

  async resumeRetailerSession(runId: string, retailerId: string, resumeToken: string): Promise<{ status: string }> {
    return this.request<{ status: string }>('/retailer-sessions/resume', {
      method: 'POST',
      body: JSON.stringify({
        run_id: runId,
        retailer_id: retailerId,
        resume_token: resumeToken,
      }),
    });
  }

  async getOrderReceipt(orderId: string): Promise<OrderConfirmationResponse> {
    return this.request<OrderConfirmationResponse>(`/orders/${orderId}`);
  }
}

export const api = new ApiClient();
