import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService, InventoryItem } from '@/services/api';
import { toast } from 'sonner';

export const INVENTORY_QUERY_KEY = 'inventory';

// Hook to get all inventory items
export const useInventoryItems = () => {
  return useQuery({
    queryKey: [INVENTORY_QUERY_KEY],
    queryFn: apiService.getInventoryItems,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
    retryDelay: 1000,
  });
};

// Hook to get a single inventory item
export const useInventoryItem = (id: string) => {
  return useQuery({
    queryKey: [INVENTORY_QUERY_KEY, id],
    queryFn: () => apiService.getInventoryItem(id),
    enabled: !!id,
  });
};

// Hook to create a new inventory item
export const useCreateInventoryItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiService.createInventoryItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVENTORY_QUERY_KEY] });
      toast.success('Item added successfully!');
    },
    onError: (error) => {
      toast.error('Failed to add item: ' + error.message);
    },
  });
};

// Hook to update an inventory item
export const useUpdateInventoryItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, item }: { id: string; item: Partial<InventoryItem> }) =>
      apiService.updateInventoryItem(id, item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVENTORY_QUERY_KEY] });
      toast.success('Item updated successfully!');
    },
    onError: (error) => {
      toast.error('Failed to update item: ' + error.message);
    },
  });
};

// Hook to delete an inventory item
export const useDeleteInventoryItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiService.deleteInventoryItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVENTORY_QUERY_KEY] });
      toast.success('Item deleted successfully!');
    },
    onError: (error) => {
      toast.error('Failed to delete item: ' + error.message);
    },
  });
};

// Hook to update quantity
export const useUpdateQuantity = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, quantity }: { id: string; quantity: number }) =>
      apiService.updateQuantity(id, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVENTORY_QUERY_KEY] });
    },
    onError: (error) => {
      toast.error('Failed to update quantity: ' + error.message);
    },
  });
};

// Hook to get inventory by category
export const useInventoryByCategory = (category: string) => {
  return useQuery({
    queryKey: [INVENTORY_QUERY_KEY, 'category', category],
    queryFn: () => apiService.getInventoryByCategory(category),
    enabled: !!category,
  });
};

// Hook to get low stock items
export const useLowStockItems = (threshold: number = 2) => {
  return useQuery({
    queryKey: [INVENTORY_QUERY_KEY, 'low-stock', threshold],
    queryFn: () => apiService.getLowStockItems(threshold),
  });
};

// Hook to get expiring items
export const useExpiringItems = (days: number = 7) => {
  return useQuery({
    queryKey: [INVENTORY_QUERY_KEY, 'expiring', days],
    queryFn: () => apiService.getExpiringItems(days),
  });
};
