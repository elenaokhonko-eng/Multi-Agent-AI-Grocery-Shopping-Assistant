const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ShoppingListItem {
  id: string;
  name: string;
  category?: string;
  desired_quantity: number;
  unit_measure: string;
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
  retailers: string[];
  items_count: number;
  created_at: string;
}

export interface QuoteLineItem {
  shopping_item_id: string;
  retailer_sku: string;
  product_title: string;
  product_brand?: string;
  unit_price_cents: number;
  packs_added: number;
  line_total_cents: number;
  is_in_stock: boolean;
  is_exact_match: boolean;
}

export interface StoreQuoteSummary {
  quote_id: string;
  retailer_id: string;
  cart_fingerprint: string;
  subtotal_cents: number;
  delivery_fee_cents: number;
  service_fee_cents: number;
  gross_total_cents: number;
  derived_net_cents: number;
  gst_cents: number;
  is_complete: boolean;
  selected_delivery_slot_id?: string;
  selected_delivery_slot_window?: string;
  expires_at: string;
  lines: QuoteLineItem[];
}

export interface ComparisonRunDetails {
  run_id: string;
  status: string;
  cheapest_complete_store?: string;
  quotes: StoreQuoteSummary[];
}

export interface ApprovalResponse {
  approval_id: string;
  approval_token: string;
  quote_id: string;
  retailer_id: string;
  gross_total_cents: number;
  delivery_slot_id: string;
  expires_at: string;
}

export interface OrderConfirmationResponse {
  order_id: string;
  retailer_order_id: string;
  retailer_id: string;
  confirmed_total_cents: number;
  confirmed_delivery_slot: string;
  receipt_url?: string;
  status: string;
  placed_at: string;
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
      let errorMessage = `HTTP ${response.status} ${response.statusText}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          errorMessage = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch (_) {}
      throw new Error(errorMessage);
    }

    if (response.status === 204) {
      return null as unknown as T;
    }

    return response.json();
  }

  getShoppingLists = (): Promise<ShoppingList[]> => {
    return this.request<ShoppingList[]>('/shopping-lists');
  };

  getShoppingList = (id: string): Promise<ShoppingList> => {
    return this.request<ShoppingList>(`/shopping-lists/${id}`);
  };

  createShoppingList = (name: string, description?: string): Promise<ShoppingList> => {
    return this.request<ShoppingList>('/shopping-lists', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
  };

  addItemToList = (listId: string, item: Partial<ShoppingListItem>): Promise<ShoppingListItem> => {
    return this.request<ShoppingListItem>(`/shopping-lists/${listId}/items`, {
      method: 'POST',
      body: JSON.stringify(item),
    });
  };

  updateItem = (listId: string, itemId: string, item: Partial<ShoppingListItem>): Promise<ShoppingListItem> => {
    return this.request<ShoppingListItem>(`/shopping-lists/${listId}/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(item),
    });
  };

  deleteItem = (listId: string, itemId: string): Promise<void> => {
    return this.request<void>(`/shopping-lists/${listId}/items/${itemId}`, {
      method: 'DELETE',
    });
  };

  startComparisonRun = (shoppingListId: string, retailerIds?: string[]): Promise<ComparisonRunInit> => {
    return this.request<ComparisonRunInit>('/comparison-runs', {
      method: 'POST',
      body: JSON.stringify({
        shopping_list_id: shoppingListId,
        retailer_ids: retailerIds || ['fairprice', 'shengsiong', 'littlefarms', 'redmart'],
      }),
    });
  };

  getComparisonRun = (runId: string): Promise<ComparisonRunDetails> => {
    return this.request<ComparisonRunDetails>(`/comparison-runs/${runId}`);
  };

  approveQuote = (quoteId: string, deliverySlotId: string): Promise<ApprovalResponse> => {
    return this.request<ApprovalResponse>(`/quotes/${quoteId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ delivery_slot_id: deliverySlotId }),
    });
  };

  submitApproval = (approvalId: string, approvalToken: string): Promise<OrderConfirmationResponse> => {
    return this.request<OrderConfirmationResponse>(`/approvals/${approvalId}/submit`, {
      method: 'POST',
      body: JSON.stringify({ approval_token: approvalToken }),
    });
  };

  getOrder = (orderId: string): Promise<OrderConfirmationResponse> => {
    return this.request<OrderConfirmationResponse>(`/orders/${orderId}`);
  };
}

export const api = new ApiClient();
