const API_BASE_URL = 'http://127.0.0.1:3005/api';

export interface InventoryItem {
  _id?: string;
  id?: number;
  name: string;
  quantity: number;
  unit: string;
  category: string;
  expiry?: string;
  createdAt?: string;
  updatedAt?: string;
}

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    console.log('Making API request to:', url);
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      console.log('API response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('API response data:', data);
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Get all inventory items
  getInventoryItems = async (): Promise<InventoryItem[]> => {
    return this.request<InventoryItem[]>('/inventory');
  }

  // Get a single inventory item by ID
  getInventoryItem = async (id: string): Promise<InventoryItem> => {
    return this.request<InventoryItem>(`/inventory/${id}`);
  }

  // Create a new inventory item
  createInventoryItem = async (item: Omit<InventoryItem, '_id' | 'id' | 'createdAt' | 'updatedAt'>): Promise<InventoryItem> => {
    return this.request<InventoryItem>('/inventory', {
      method: 'POST',
      body: JSON.stringify(item),
    });
  }

  // Update an existing inventory item
  updateInventoryItem = async (id: string, item: Partial<InventoryItem>): Promise<InventoryItem> => {
    return this.request<InventoryItem>(`/inventory/${id}`, {
      method: 'PUT',
      body: JSON.stringify(item),
    });
  }

  // Delete an inventory item
  deleteInventoryItem = async (id: string): Promise<void> => {
    return this.request<void>(`/inventory/${id}`, {
      method: 'DELETE',
    });
  }

  // Update quantity of an inventory item
  updateQuantity = async (id: string, quantity: number): Promise<InventoryItem> => {
    return this.request<InventoryItem>(`/inventory/${id}/quantity`, {
      method: 'PATCH',
      body: JSON.stringify({ quantity }),
    });
  }

  // Get inventory items by category
  getInventoryByCategory = async (category: string): Promise<InventoryItem[]> => {
    return this.request<InventoryItem[]>(`/inventory/category/${category}`);
  }

  // Get low stock items
  getLowStockItems = async (threshold: number = 2): Promise<InventoryItem[]> => {
    return this.request<InventoryItem[]>(`/inventory/low-stock?threshold=${threshold}`);
  }

  // Get expiring items
  getExpiringItems = async (days: number = 7): Promise<InventoryItem[]> => {
    return this.request<InventoryItem[]>(`/inventory/expiring?days=${days}`);
  }
}

export const apiService = new ApiService();
