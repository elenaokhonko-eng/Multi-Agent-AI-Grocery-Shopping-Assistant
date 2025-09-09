import { useState } from 'react';
import { Plus, Minus, X, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  useInventoryItems,
  useCreateInventoryItem,
  useDeleteInventoryItem,
  useUpdateQuantity,
} from '@/hooks/useInventory';

const CATEGORIES = ['Grains', 'Dairy', 'Vegetables', 'Fruits', 'Meat', 'Seafood', 'Spices', 'Beverages', 'Snacks', 'Other'];
const UNITS = ['pieces', 'kg', 'grams', 'liters', 'ml', 'cups', 'tbsp', 'tsp', 'lbs', 'oz'];

type KitchenInventoryProps = {
  /** Hide the small internal header when you already show a page H1 outside. */
  showHeader?: boolean;
};

export const KitchenInventory = ({ showHeader = true }: KitchenInventoryProps) => {
  // Full-page (no expand/collapse)
  const [newItem, setNewItem] = useState({
    name: '',
    quantity: '',
    unit: 'pieces',
    category: 'Other',
    expiry: '',
  });

  // React Query hooks
  const { data: inventory = [], isLoading, error } = useInventoryItems();
  const createItemMutation = useCreateInventoryItem();
  const deleteItemMutation = useDeleteInventoryItem();
  const updateQuantityMutation = useUpdateQuantity();

  const addItem = async () => {
    const qty = Number(newItem.quantity);
    if (!newItem.name.trim() || Number.isNaN(qty) || qty <= 0) return;

    try {
      await createItemMutation.mutateAsync({
        name: newItem.name.trim(),
        quantity: qty,
        unit: newItem.unit || 'pieces',
        category: newItem.category,
        ...(newItem.expiry && { expiry: newItem.expiry }),
      });
      setNewItem({ name: '', quantity: '', unit: 'pieces', category: 'Other', expiry: '' });
    } catch (e) {
      console.error('Failed to add item:', e);
    }
  };

  const updateQuantity = async (id: string, change: number) => {
    const item = inventory.find((it: any) => it._id === id || it.id?.toString() === id);
    if (!item) return;

    const next = Math.max(0, Number(item.quantity) + change);
    if (next === 0) {
      await deleteItemMutation.mutateAsync(id);
    } else {
      await updateQuantityMutation.mutateAsync({ id, quantity: next });
    }
  };

  const removeItem = async (id: string) => {
    try {
      await deleteItemMutation.mutateAsync(id);
    } catch (e) {
      console.error('Failed to remove item:', e);
    }
  };

  // Helpers
  const isExpiringSoon = (expiry?: string) => {
    if (!expiry) return false;
    const expiryDate = new Date(expiry);
    const today = new Date();
    const days = Math.ceil((expiryDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return days <= 7 && days >= 0;
  };

  const isExpired = (expiry?: string) => {
    if (!expiry) return false;
    const expiryDate = new Date(expiry);
    const today = new Date();
    return expiryDate < today;
  };

  const categories = Array.from(new Set(inventory.map((it: any) => it.category || 'Other')));
  const totalItems = inventory.reduce((sum: number, it: any) => sum + Number(it.quantity || 0), 0);

  // States
  if (isLoading) {
    return <div className="w-full p-4 text-center text-muted-foreground">Loading inventory...</div>;
  }

  if (error) {
    return (
      <div className="w-full p-4 text-center">
        <p className="text-destructive">Failed to load inventory</p>
        <p className="text-sm text-muted-foreground">Check if the backend server is running</p>
      </div>
    );
  }

  // Full-page layout
  return (
    <div className="w-full space-y-4">
      {/* Small internal header (optional) */}
      {showHeader && (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Package className="h-5 w-5 text-accent" />
              <h3 className="text-xl font-semibold">Kitchen Inventory</h3>
            </div>
            <div className="text-sm text-muted-foreground">
              <span>{inventory.length} items</span>
              <span className="mx-2">•</span>
              <span>Total: {totalItems}</span>
            </div>
          </div>
          <Separator />
        </>
      )}

      {/* Add New Item */}
      <Card className="border-accent/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Add New Item</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Input
            placeholder="Item name"
            value={newItem.name}
            onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
            onKeyDown={(e) => e.key === 'Enter' && addItem()}
            className="text-sm"
          />
          <div className="flex gap-2">
            <Input
              placeholder="Qty"
              type="number"
              value={newItem.quantity}
              onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })}
              onKeyDown={(e) => e.key === 'Enter' && addItem()}
              className="text-sm flex-1"
            />
            <Select value={newItem.unit} onValueChange={(val) => setNewItem({ ...newItem, unit: val })}>
              <SelectTrigger className="text-sm flex-1">
                <SelectValue placeholder="Unit" />
              </SelectTrigger>
              <SelectContent className="bg-background border border-border shadow-lg z-50">
                {UNITS.map((u) => (
                  <SelectItem key={u} value={u} className="text-sm">
                    {u}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Select value={newItem.category} onValueChange={(val) => setNewItem({ ...newItem, category: val })}>
            <SelectTrigger className="text-sm">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent className="bg-background border border-border shadow-lg z-50">
              {CATEGORIES.map((c) => (
                <SelectItem key={c} value={c} className="text-sm">
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Input
            placeholder="Expiry date (optional)"
            type="date"
            value={newItem.expiry}
            onChange={(e) => setNewItem({ ...newItem, expiry: e.target.value })}
            className="text-sm"
          />

          <Button
            onClick={addItem}
            className="w-full bg-gradient-primary border-0"
            size="sm"
            disabled={createItemMutation.isPending}
          >
            <Plus className="h-4 w-4 mr-1" />
            {createItemMutation.isPending ? 'Adding...' : 'Add Item'}
          </Button>
        </CardContent>
      </Card>

      {/* Empty state */}
      {inventory.length === 0 ? (
        <Card className="border-dashed border-muted">
          <CardContent className="p-6 text-center space-y-3">
            <p className="text-sm text-muted-foreground">
              Your inventory is empty. Add an item above or use a quick add:
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {[
                { name: 'Rice', qty: 1, unit: 'kg', category: 'Grains' },
                { name: 'Milk', qty: 1, unit: 'liters', category: 'Dairy' },
                { name: 'Eggs', qty: 12, unit: 'pieces', category: 'Other' },
              ].map((q) => (
                <Button
                  key={q.name}
                  size="sm"
                  variant="secondary"
                  onClick={() =>
                    createItemMutation.mutate({
                      name: q.name,
                      quantity: q.qty,
                      unit: q.unit,
                      category: q.category,
                    })
                  }
                  disabled={createItemMutation.isPending}
                >
                  + {q.name}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        /* Inventory by Category */
        <div className="space-y-4">
          {categories.map((category) => (
            <div key={category} className="space-y-2">
              <h4 className="font-medium text-sm text-accent">{category}</h4>
              <div className="space-y-2">
                {inventory
                  .filter((it: any) => (it.category || 'Other') === category)
                  .map((it: any) => {
                    const itemId = (it._id as string) || it.id?.toString() || '';
                    return (
                      <Card key={itemId} className="border-border/50">
                        <CardContent className="p-3">
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <h5 className="font-medium text-sm truncate">{it.name}</h5>
                                {isExpired(it.expiry) && (
                                  <Badge variant="destructive" className="text-xs">
                                    Expired
                                  </Badge>
                                )}
                                {isExpiringSoon(it.expiry) && !isExpired(it.expiry) && (
                                  <Badge className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200">
                                    Soon
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-muted-foreground">
                                {it.quantity} {it.unit}
                                {it.expiry && (
                                  <span className="ml-2">• Exp: {new Date(it.expiry).toLocaleDateString()}</span>
                                )}
                              </p>
                            </div>
                            <div className="flex items-center gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => updateQuantity(itemId, -1)}
                                className="h-6 w-6 p-0"
                                disabled={updateQuantityMutation.isPending}
                              >
                                <Minus className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => updateQuantity(itemId, 1)}
                                className="h-6 w-6 p-0"
                                disabled={updateQuantityMutation.isPending}
                              >
                                <Plus className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => removeItem(itemId)}
                                className="h-6 w-6 p-0 text-destructive"
                                disabled={deleteItemMutation.isPending}
                              >
                                <X className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Quick Stats */}
      <Card className="bg-gradient-secondary border-0">
        <CardContent className="p-3">
          <div className="text-center space-y-1">
            <h4 className="font-medium text-sm">Inventory Status</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <p className="font-medium">
                  {inventory.filter((it: any) => isExpiringSoon(it.expiry)).length}
                </p>
                <p className="text-muted-foreground">Expiring Soon</p>
              </div>
              <div>
                <p className="font-medium">
                  {inventory.filter((it: any) => Number(it.quantity) < 2).length}
                </p>
                <p className="text-muted-foreground">Running Low</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
