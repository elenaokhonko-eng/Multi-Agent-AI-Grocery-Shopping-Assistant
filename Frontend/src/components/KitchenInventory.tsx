import { useState } from 'react';
import { Plus, Minus, X, ChefHat, Package, ChevronRight, ChevronLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  useInventoryItems, 
  useCreateInventoryItem, 
  useUpdateInventoryItem, 
  useDeleteInventoryItem,
  useUpdateQuantity 
} from '@/hooks/useInventory';
import { InventoryItem } from '@/services/api';

const CATEGORIES = ['Grains', 'Dairy', 'Vegetables', 'Fruits', 'Meat', 'Seafood', 'Spices', 'Beverages', 'Snacks', 'Other'];
const UNITS = ['pieces', 'kg', 'grams', 'liters', 'ml', 'cups', 'tbsp', 'tsp', 'lbs', 'oz'];

export const KitchenInventory = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [newItem, setNewItem] = useState({ name: '', quantity: '', unit: 'pieces', category: 'Other', expiry: '' });

  // React Query hooks for data fetching and mutations
  const { data: inventory = [], isLoading, error } = useInventoryItems();
  const createItemMutation = useCreateInventoryItem();
  const updateItemMutation = useUpdateInventoryItem();
  const deleteItemMutation = useDeleteInventoryItem();
  const updateQuantityMutation = useUpdateQuantity();

  const addItem = async () => {
    if (newItem.name && newItem.quantity) {
      try {
        await createItemMutation.mutateAsync({
          name: newItem.name,
          quantity: parseFloat(newItem.quantity),
          unit: newItem.unit || 'pieces',
          category: newItem.category,
          ...(newItem.expiry && { expiry: newItem.expiry })
        });
        setNewItem({ name: '', quantity: '', unit: 'pieces', category: 'Other', expiry: '' });
      } catch (error) {
        console.error('Failed to add item:', error);
      }
    }
  };

  const updateQuantity = async (id: string, change: number) => {
    const item = inventory.find(item => item._id === id || item.id?.toString() === id);
    if (item) {
      const newQuantity = Math.max(0, item.quantity + change);
      if (newQuantity === 0) {
        await deleteItemMutation.mutateAsync(id);
      } else {
        await updateQuantityMutation.mutateAsync({ id, quantity: newQuantity });
      }
    }
  };

  const removeItem = async (id: string) => {
    try {
      await deleteItemMutation.mutateAsync(id);
    } catch (error) {
      console.error('Failed to remove item:', error);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className={`transition-all duration-300 ${isExpanded ? 'w-80' : 'w-16'} bg-white border-l shadow-soft`}>
        <div className="p-4 border-b">
          <Button
            variant="ghost"
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-center hover:bg-accent/10"
          >
            {isExpanded ? (
              <>
                <ChevronRight className="h-5 w-5" />
                <span className="ml-2">Hide Inventory</span>
              </>
            ) : (
              <ChefHat className="h-5 w-5 text-accent" />
            )}
          </Button>
        </div>
        {isExpanded && (
          <div className="p-4 text-center">
            <p className="text-muted-foreground">Loading inventory...</p>
          </div>
        )}
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className={`transition-all duration-300 ${isExpanded ? 'w-80' : 'w-16'} bg-white border-l shadow-soft`}>
        <div className="p-4 border-b">
          <Button
            variant="ghost"
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-center hover:bg-accent/10"
          >
            {isExpanded ? (
              <>
                <ChevronRight className="h-5 w-5" />
                <span className="ml-2">Hide Inventory</span>
              </>
            ) : (
              <ChefHat className="h-5 w-5 text-accent" />
            )}
          </Button>
        </div>
        {isExpanded && (
          <div className="p-4 text-center">
            <p className="text-destructive">Failed to load inventory</p>
            <p className="text-sm text-muted-foreground">Check if the backend server is running</p>
          </div>
        )}
      </div>
    );
  }

  const categories = Array.from(new Set(inventory.map(item => item.category)));
  const totalItems = inventory.reduce((sum, item) => sum + item.quantity, 0);

  const isExpiringSoon = (expiry?: string) => {
    if (!expiry) return false;
    const expiryDate = new Date(expiry);
    const today = new Date();
    const daysUntilExpiry = Math.ceil((expiryDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return daysUntilExpiry <= 7 && daysUntilExpiry >= 0;
  };

  const isExpired = (expiry?: string) => {
    if (!expiry) return false;
    const expiryDate = new Date(expiry);
    const today = new Date();
    return expiryDate < today;
  };

  return (
    <div className={`transition-all duration-300 ${isExpanded ? 'w-80' : 'w-16'} bg-white border-l shadow-soft`}>
      {/* Toggle Button */}
      <div className="p-4 border-b">
        <Button
          variant="ghost"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-center hover:bg-accent/10"
        >
          {isExpanded ? (
            <>
              <ChevronRight className="h-5 w-5" />
              <span className="ml-2">Hide Inventory</span>
            </>
          ) : (
            <ChefHat className="h-5 w-5 text-accent" />
          )}
        </Button>
      </div>

      {isExpanded && (
        <div className="p-4 space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto">
          {/* Header */}
          <div className="space-y-2">
            <h3 className="font-semibold text-lg flex items-center">
              <Package className="h-5 w-5 mr-2 text-accent" />
              Kitchen Inventory
            </h3>
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>{inventory.length} items</span>
              <span>Total: {totalItems}</span>
            </div>
          </div>

          <Separator />

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
                className="text-sm"
              />
              <div className="flex space-x-2">
                <Input
                  placeholder="Qty"
                  type="number"
                  value={newItem.quantity}
                  onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })}
                  className="text-sm flex-1"
                />
                <Select value={newItem.unit} onValueChange={(value) => setNewItem({ ...newItem, unit: value })}>
                  <SelectTrigger className="text-sm flex-1">
                    <SelectValue placeholder="Unit" />
                  </SelectTrigger>
                  <SelectContent className="bg-background border border-border shadow-lg z-50">
                    {UNITS.map(unit => (
                      <SelectItem key={unit} value={unit} className="text-sm">
                        {unit}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Select value={newItem.category} onValueChange={(value) => setNewItem({ ...newItem, category: value })}>
                <SelectTrigger className="text-sm">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent className="bg-background border border-border shadow-lg z-50">
                  {CATEGORIES.map(category => (
                    <SelectItem key={category} value={category} className="text-sm">
                      {category}
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

          {/* Inventory by Category */}
          <div className="space-y-3">
            {categories.map(category => (
              <div key={category} className="space-y-2">
                <h4 className="font-medium text-sm text-accent">{category}</h4>
                <div className="space-y-1">
                  {inventory
                    .filter(item => item.category === category)
                    .map(item => {
                      const itemId = item._id || item.id?.toString() || '';
                      return (
                        <Card key={itemId} className="border-border/50">
                          <CardContent className="p-3">
                            <div className="flex items-center justify-between">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center space-x-2">
                                  <h5 className="font-medium text-sm truncate">{item.name}</h5>
                                  {isExpired(item.expiry) && (
                                    <Badge variant="destructive" className="text-xs">Expired</Badge>
                                  )}
                                  {isExpiringSoon(item.expiry) && !isExpired(item.expiry) && (
                                    <Badge variant="destructive" className="text-xs bg-warning">Soon</Badge>
                                  )}
                                </div>
                                <p className="text-xs text-muted-foreground">
                                  {item.quantity} {item.unit}
                                  {item.expiry && (
                                    <span className="ml-2">• Exp: {new Date(item.expiry).toLocaleDateString()}</span>
                                  )}
                                </p>
                              </div>
                              <div className="flex items-center space-x-1">
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
                    })
                  }
                </div>
              </div>
            ))}
          </div>

          {/* Quick Stats */}
          <Card className="bg-gradient-secondary border-0">
            <CardContent className="p-3">
              <div className="text-center space-y-1">
                <h4 className="font-medium text-sm">Inventory Status</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <p className="font-medium">{inventory.filter(item => isExpiringSoon(item.expiry)).length}</p>
                    <p className="text-muted-foreground">Expiring Soon</p>
                  </div>
                  <div>
                    <p className="font-medium">{inventory.filter(item => item.quantity < 2).length}</p>
                    <p className="text-muted-foreground">Running Low</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};