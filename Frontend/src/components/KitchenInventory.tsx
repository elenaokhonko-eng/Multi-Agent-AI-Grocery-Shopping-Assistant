import { useState } from 'react';
import { Plus, Minus, X, ChefHat, Package, ChevronRight, ChevronLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface InventoryItem {
  id: number;
  name: string;
  quantity: number;
  unit: string;
  category: string;
  expiry?: string;
}

const initialInventory: InventoryItem[] = [
  { id: 1, name: "Rice", quantity: 5, unit: "kg", category: "Grains", expiry: "2024-12-01" },
  { id: 2, name: "Milk", quantity: 2, unit: "liters", category: "Dairy", expiry: "2024-01-15" },
  { id: 3, name: "Eggs", quantity: 12, unit: "pieces", category: "Dairy" },
  { id: 4, name: "Onions", quantity: 3, unit: "kg", category: "Vegetables" },
  { id: 5, name: "Tomatoes", quantity: 1.5, unit: "kg", category: "Vegetables", expiry: "2024-01-10" },
  { id: 6, name: "Chicken", quantity: 2, unit: "kg", category: "Meat", expiry: "2024-01-08" }
];

const CATEGORIES = ['Grains', 'Dairy', 'Vegetables', 'Fruits', 'Meat', 'Seafood', 'Spices', 'Beverages', 'Snacks', 'Other'];
const UNITS = ['pieces', 'kg', 'grams', 'liters', 'ml', 'cups', 'tbsp', 'tsp', 'lbs', 'oz'];

export const KitchenInventory = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [inventory, setInventory] = useState<InventoryItem[]>(initialInventory);
  const [newItem, setNewItem] = useState({ name: '', quantity: '', unit: 'pieces', category: 'Other' });

  const addItem = () => {
    if (newItem.name && newItem.quantity) {
      const item: InventoryItem = {
        id: Date.now(),
        name: newItem.name,
        quantity: parseFloat(newItem.quantity),
        unit: newItem.unit || 'pieces',
        category: newItem.category
      };
      setInventory([...inventory, item]);
      setNewItem({ name: '', quantity: '', unit: 'pieces', category: 'Other' });
    }
  };

  const updateQuantity = (id: number, change: number) => {
    setInventory(inventory.map(item => 
      item.id === id 
        ? { ...item, quantity: Math.max(0, item.quantity + change) }
        : item
    ).filter(item => item.quantity > 0));
  };

  const removeItem = (id: number) => {
    setInventory(inventory.filter(item => item.id !== id));
  };

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
              <Button 
                onClick={addItem} 
                className="w-full bg-gradient-primary border-0"
                size="sm"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Item
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
                    .map(item => (
                      <Card key={item.id} className="border-border/50">
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
                                onClick={() => updateQuantity(item.id, -1)}
                                className="h-6 w-6 p-0"
                              >
                                <Minus className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => updateQuantity(item.id, 1)}
                                className="h-6 w-6 p-0"
                              >
                                <Plus className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => removeItem(item.id)}
                                className="h-6 w-6 p-0 text-destructive"
                              >
                                <X className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))
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