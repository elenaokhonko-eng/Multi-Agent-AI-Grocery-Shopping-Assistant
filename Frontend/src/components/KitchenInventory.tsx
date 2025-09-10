import { useState, useMemo } from 'react';
import { Plus, Minus, X, Package, Calendar, Search, Filter, SlidersHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Checkbox } from '@/components/ui/checkbox';
import {
  useInventoryItems,
  useCreateInventoryItem,
  useDeleteInventoryItem,
  useUpdateQuantity,
} from '@/hooks/useInventory';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { toast } from 'sonner';

const CATEGORIES = ['Grains', 'Dairy', 'Vegetables', 'Fruits', 'Meat', 'Seafood', 'Spices', 'Beverages', 'Snacks', 'Other'];
const UNITS = ['pieces', 'kg', 'grams', 'liters', 'ml', 'cups', 'tbsp', 'tsp', 'lbs', 'oz'];
const LOW_STOCK_THRESHOLD = 2;

/* ---------- helpers ---------- */
const daysUntil = (dateStr?: string) => {
  if (!dateStr) return undefined;
  const target = new Date(dateStr);
  const today = new Date();
  return Math.ceil((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
};
const isSoon = (dateStr?: string) => {
  const d = daysUntil(dateStr);
  return typeof d === 'number' && d <= 7 && d >= 0;
};
const isExpired = (dateStr?: string) => {
  if (!dateStr) return false;
  const target = new Date(dateStr);
  const today = new Date();
  return target < today;
};

/* ---------- Item row component ---------- */
type RowProps = {
  item: any;
  busy?: boolean;
  onInc: () => void;
  onDec: () => void;
  onDelete: () => void;
};
function InventoryItemRow({ item, busy, onInc, onDec, onDelete }: RowProps) {
  const id = (item._id as string) || item.id?.toString() || '';
  const qty = Number(item.quantity) || 0;
  const unit = item.unit || 'pieces';
  const soon = isSoon(item.expiry);
  const expired = isExpired(item.expiry);
  const low = qty < LOW_STOCK_THRESHOLD;

  return (
    <Card key={id} className="group relative overflow-hidden bg-white/60 backdrop-blur-sm border border-white/20 hover:border-white/40 transition-all duration-500 hover:shadow-xl hover:-translate-y-1 rounded-2xl animate-fade-in">
      {/* Gradient background that appears on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 via-white/30 to-purple-50/50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
      
      {/* Status indicator bar */}
      <div className={`absolute top-0 left-0 right-0 h-1 transition-all duration-300 ${
        expired ? 'bg-gradient-to-r from-red-500 to-red-600' :
        soon ? 'bg-gradient-to-r from-amber-400 to-orange-500' :
        low ? 'bg-gradient-to-r from-blue-400 to-cyan-500' :
        'bg-gradient-to-r from-green-400 to-emerald-500'
      }`}></div>
      
      <CardContent className="relative z-10 p-4">
        <div className="flex items-center justify-between gap-4">
          {/* Left: Item info with enhanced styling */}
          <div className="flex-1 min-w-0 space-y-2">
            {/* Item name and badges */}
            <div className="flex items-center gap-3 flex-wrap">
              <h5 className="font-semibold text-gray-800 group-hover:text-gray-900 transition-colors truncate text-base">
                {item.name}
              </h5>
              
              {/* Status badges with modern styling */}
              <div className="flex gap-2">
                {expired && (
                  <Badge className="text-xs px-2 py-1 bg-gradient-to-r from-red-500 to-red-600 text-white border-0 rounded-full animate-pulse">
                    Expired
                  </Badge>
                )}
                {!expired && soon && (
                  <Badge className="text-xs px-2 py-1 bg-gradient-to-r from-amber-400 to-orange-500 text-white border-0 rounded-full">
                    Soon
                  </Badge>
                )}
                {!expired && !soon && low && (
                  <Badge className="text-xs px-2 py-1 bg-gradient-to-r from-blue-400 to-cyan-500 text-white border-0 rounded-full">
                    Low Stock
                  </Badge>
                )}
              </div>
            </div>
            
            {/* Quantity and expiry info */}
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full"></div>
                <span className="font-medium">{qty} {unit}</span>
              </div>
              
              {item.expiry && (
                <div className="flex items-center gap-2 text-gray-500">
                  <Calendar className="h-3 w-3" />
                  <span>
                    Exp: {new Date(item.expiry).toLocaleDateString()}
                    {typeof daysUntil(item.expiry) === 'number' && (
                      <span className="ml-1 text-xs bg-gray-100 px-1.5 py-0.5 rounded-full">
                        {daysUntil(item.expiry)}d
                      </span>
                    )}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* right: qty control + delete */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Enhanced quantity control */}
            <div className="flex items-center bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200/60 overflow-hidden shadow-sm group-hover:shadow-md transition-shadow duration-300">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-none hover:bg-white/60 text-gray-600 hover:text-gray-800 transition-all duration-200"
                onClick={onDec}
                disabled={busy || qty <= 0}
                aria-label="Decrease quantity"
              >
                <Minus className="h-4 w-4" />
              </Button>
              <div className="px-4 py-2 text-sm font-semibold text-gray-800 bg-white/40 min-w-[3rem] text-center tabular-nums">
                {qty}
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-none hover:bg-white/60 text-gray-600 hover:text-gray-800 transition-all duration-200"
                onClick={onInc}
                disabled={busy}
                aria-label="Increase quantity"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {/* delete with confirm */}
            <AlertDialog>
              <Tooltip>
                <TooltipTrigger asChild>
                  <AlertDialogTrigger asChild>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive"
                      disabled={busy}
                      aria-label="Delete item"
                    >
                      <X className="h-3.5 w-3.5" />
                    </Button>
                  </AlertDialogTrigger>
                </TooltipTrigger>
                <TooltipContent>Delete</TooltipContent>
              </Tooltip>

              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete “{item.name}”?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This action cannot be undone. The item will be removed from your inventory.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    className="bg-destructive text-destructive-foreground hover:opacity-90"
                    onClick={onDelete}
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </CardContent>
      
      {/* Subtle hover glow effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-400/10 to-purple-400/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
    </Card>
  );
}

/* ---------- Main component ---------- */
type KitchenInventoryProps = { showHeader?: boolean };

export const KitchenInventory = ({ showHeader = true }: KitchenInventoryProps) => {
  const [newItem, setNewItem] = useState({
    name: '',
    quantity: '',
    unit: 'pieces',
    category: 'Other',
    expiry: '',
  });

  // Filter and search states
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [statusFilters, setStatusFilters] = useState({
    lowStock: false,
    expiringSoon: false,
    expired: false,
  });
  const [sortBy, setSortBy] = useState<'name' | 'quantity' | 'expiry' | 'category'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const { data: inventory = [], isLoading, error } = useInventoryItems();
  const createItemMutation = useCreateInventoryItem();
  const deleteItemMutation = useDeleteInventoryItem();
  const updateQuantityMutation = useUpdateQuantity();

  const busy = createItemMutation.isPending || deleteItemMutation.isPending || updateQuantityMutation.isPending;

  // Filtered and sorted inventory
  const filteredInventory = useMemo(() => {
    let filtered = inventory.filter((item: any) => {
      // Search filter
      const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());
      
      // Category filter
      const itemCategory = item.category || 'Other';
      const matchesCategory = selectedCategories.length === 0 || selectedCategories.includes(itemCategory);
      
      // Status filters
      const isLowStock = Number(item.quantity) < LOW_STOCK_THRESHOLD;
      const isExpiringSoon = isSoon(item.expiry);
      const isExpiredItem = isExpired(item.expiry);
      
      const hasStatusFilter = statusFilters.lowStock || statusFilters.expiringSoon || statusFilters.expired;
      const matchesStatus = !hasStatusFilter || 
        (statusFilters.lowStock && isLowStock) ||
        (statusFilters.expiringSoon && isExpiringSoon) ||
        (statusFilters.expired && isExpiredItem);

      return matchesSearch && matchesCategory && matchesStatus;
    });

    // Sorting
    filtered.sort((a: any, b: any) => {
      let compareValue = 0;
      
      switch (sortBy) {
        case 'name':
          compareValue = a.name.localeCompare(b.name);
          break;
        case 'quantity':
          compareValue = Number(a.quantity) - Number(b.quantity);
          break;
        case 'expiry':
          if (!a.expiry && !b.expiry) compareValue = 0;
          else if (!a.expiry) compareValue = 1;
          else if (!b.expiry) compareValue = -1;
          else compareValue = new Date(a.expiry).getTime() - new Date(b.expiry).getTime();
          break;
        case 'category':
          compareValue = (a.category || 'Other').localeCompare(b.category || 'Other');
          break;
      }
      
      return sortOrder === 'asc' ? compareValue : -compareValue;
    });

    return filtered;
  }, [inventory, searchTerm, selectedCategories, statusFilters, sortBy, sortOrder]);

  const resetForm = () =>
    setNewItem({ name: '', quantity: '', unit: 'pieces', category: 'Other', expiry: '' });

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedCategories([]);
    setStatusFilters({ lowStock: false, expiringSoon: false, expired: false });
    setSortBy('name');
    setSortOrder('asc');
  };

  const addItem = async () => {
    const qty = Number(newItem.quantity);
    if (!newItem.name.trim()) return toast.error('Please enter an item name');
    if (Number.isNaN(qty) || qty <= 0) return toast.error('Quantity must be greater than 0');

    try {
      await createItemMutation.mutateAsync({
        name: newItem.name.trim(),
        quantity: qty,
        unit: newItem.unit,
        category: newItem.category,
        ...(newItem.expiry && { expiry: newItem.expiry }),
      });
      toast.success('Item added');
      resetForm();
    } catch (e) {
      console.error(e);
      toast.error('Failed to add item');
    }
  };

  const bumpQtyLocal = (delta: number) =>
    setNewItem((s) => ({ ...s, quantity: String(Math.max(0, Number(s.quantity || 0) + delta)) }));

  const updateQuantity = async (id: string, change: number) => {
    const item = inventory.find((it: any) => it._id === id || it.id?.toString() === id);
    if (!item) return;
    const next = Math.max(0, Number(item.quantity) + change);

    try {
      if (next === 0) {
        await deleteItemMutation.mutateAsync(id);
        toast.success('Item removed');
      } else {
        await updateQuantityMutation.mutateAsync({ id, quantity: next });
      }
    } catch (e) {
      console.error(e);
      toast.error('Failed to update quantity');
    }
  };

  const removeItem = async (id: string) => {
    try {
      await deleteItemMutation.mutateAsync(id);
      toast.success('Item removed');
    } catch (e) {
      console.error(e);
      toast.error('Failed to remove item');
    }
  };

  const categories = Array.from(new Set(inventory.map((it: any) => it.category || 'Other')));
  const totalItems = inventory.reduce((sum: number, it: any) => sum + Number(it.quantity || 0), 0);
  const filteredItemsCount = filteredInventory.length;
  const hasActiveFilters = searchTerm || selectedCategories.length > 0 || 
    statusFilters.lowStock || statusFilters.expiringSoon || statusFilters.expired;

  // Count items by status
  const lowStockCount = inventory.filter((it: any) => Number(it.quantity) < LOW_STOCK_THRESHOLD).length;
  const expiringSoonCount = inventory.filter((it: any) => isSoon(it.expiry)).length;
  const expiredCount = inventory.filter((it: any) => isExpired(it.expiry)).length;

  if (isLoading) return <div className="w-full p-4 text-center text-muted-foreground">Loading inventory...</div>;
  if (error) {
    return (
      <div className="w-full p-4 text-center">
        <p className="text-destructive">Failed to load inventory</p>
        <p className="text-sm text-muted-foreground">Check if the backend server is running</p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-4">
      {/* mini header */}
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

      {/* Search and Filters - Modern Design */}
      <Card className="relative overflow-hidden bg-white/70 backdrop-blur-xl border border-white/30 shadow-lg rounded-3xl">
        {/* Animated background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/30 via-white/20 to-purple-50/30"></div>
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-cyan-200/20 to-blue-200/20 rounded-full blur-2xl"></div>
        
        <CardContent className="relative z-10 p-6 space-y-6">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search inventory items..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Category Filter */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="gap-2">
                  <Filter className="h-4 w-4" />
                  Categories
                  {selectedCategories.length > 0 && (
                    <Badge variant="secondary" className="ml-1">
                      {selectedCategories.length}
                    </Badge>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-56">
                <div className="space-y-3">
                  <h4 className="font-medium text-sm">Filter by Category</h4>
                  <div className="space-y-2">
                    {categories.map((category) => (
                      <div key={category} className="flex items-center space-x-2">
                        <Checkbox
                          id={`category-${category}`}
                          checked={selectedCategories.includes(category)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedCategories([...selectedCategories, category]);
                            } else {
                              setSelectedCategories(selectedCategories.filter(c => c !== category));
                            }
                          }}
                        />
                        <label 
                          htmlFor={`category-${category}`}
                          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                        >
                          {category}
                        </label>
                      </div>
                    ))}
                  </div>
                  {selectedCategories.length > 0 && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => setSelectedCategories([])}
                      className="w-full"
                    >
                      Clear Categories
                    </Button>
                  )}
                </div>
              </PopoverContent>
            </Popover>

            {/* Status Filter */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="gap-2">
                  <SlidersHorizontal className="h-4 w-4" />
                  Status
                  {(statusFilters.lowStock || statusFilters.expiringSoon || statusFilters.expired) && (
                    <Badge variant="secondary" className="ml-1">
                      {Object.values(statusFilters).filter(Boolean).length}
                    </Badge>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-56">
                <div className="space-y-3">
                  <h4 className="font-medium text-sm">Filter by Status</h4>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="low-stock"
                        checked={statusFilters.lowStock}
                        onCheckedChange={(checked) => 
                          setStatusFilters(prev => ({ ...prev, lowStock: checked as boolean }))
                        }
                      />
                      <label htmlFor="low-stock" className="text-sm font-medium leading-none cursor-pointer">
                        Low Stock ({lowStockCount})
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="expiring-soon"
                        checked={statusFilters.expiringSoon}
                        onCheckedChange={(checked) => 
                          setStatusFilters(prev => ({ ...prev, expiringSoon: checked as boolean }))
                        }
                      />
                      <label htmlFor="expiring-soon" className="text-sm font-medium leading-none cursor-pointer">
                        Expiring Soon ({expiringSoonCount})
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="expired"
                        checked={statusFilters.expired}
                        onCheckedChange={(checked) => 
                          setStatusFilters(prev => ({ ...prev, expired: checked as boolean }))
                        }
                      />
                      <label htmlFor="expired" className="text-sm font-medium leading-none cursor-pointer">
                        Expired ({expiredCount})
                      </label>
                    </div>
                  </div>
                  {(statusFilters.lowStock || statusFilters.expiringSoon || statusFilters.expired) && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => setStatusFilters({ lowStock: false, expiringSoon: false, expired: false })}
                      className="w-full"
                    >
                      Clear Status Filters
                    </Button>
                  )}
                </div>
              </PopoverContent>
            </Popover>

            {/* Sort */}
            <div className="flex gap-2">
              <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="name">Name</SelectItem>
                  <SelectItem value="quantity">Quantity</SelectItem>
                  <SelectItem value="expiry">Expiry</SelectItem>
                  <SelectItem value="category">Category</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </Button>
            </div>
          </div>

          {/* Active filters summary */}
          {hasActiveFilters && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-muted-foreground">Active filters:</span>
              {searchTerm && (
                <Badge variant="secondary" className="gap-1">
                  Search: "{searchTerm}"
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => setSearchTerm('')}
                  />
                </Badge>
              )}
              {selectedCategories.map(category => (
                <Badge key={category} variant="secondary" className="gap-1">
                  {category}
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => setSelectedCategories(prev => prev.filter(c => c !== category))}
                  />
                </Badge>
              ))}
              {statusFilters.lowStock && (
                <Badge variant="secondary" className="gap-1">
                  Low Stock
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => setStatusFilters(prev => ({ ...prev, lowStock: false }))}
                  />
                </Badge>
              )}
              {statusFilters.expiringSoon && (
                <Badge variant="secondary" className="gap-1">
                  Expiring Soon
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => setStatusFilters(prev => ({ ...prev, expiringSoon: false }))}
                  />
                </Badge>
              )}
              {statusFilters.expired && (
                <Badge variant="secondary" className="gap-1">
                  Expired
                  <X 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => setStatusFilters(prev => ({ ...prev, expired: false }))}
                  />
                </Badge>
              )}
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                Clear All
              </Button>
            </div>
          )}

          {/* Results count */}
          <div className="text-sm text-muted-foreground">
            Showing {filteredItemsCount} of {inventory.length} items
            {hasActiveFilters && (
              <span className="ml-2 text-accent">• Filtered results</span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Add New Item Form - Modern Design */}
      <Card className="relative overflow-hidden bg-gradient-to-br from-white/80 to-blue-50/50 backdrop-blur-xl border border-white/40 shadow-xl rounded-3xl">
        {/* Animated background elements */}
        <div className="absolute top-0 left-0 w-24 h-24 bg-gradient-to-br from-green-200/30 to-emerald-200/30 rounded-full blur-xl"></div>
        <div className="absolute bottom-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-200/30 to-purple-200/30 rounded-full blur-xl"></div>
        
        <CardHeader className="relative z-10 pb-4">
          <CardTitle className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent">
            Add New Item
          </CardTitle>
        </CardHeader>
        <CardContent className="relative z-10 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            <div className="md:col-span-12">
              <label className="block text-xs font-medium mb-1">Item name</label>
              <Input
                placeholder="e.g., Basmati Rice"
                value={newItem.name}
                onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
                onKeyDown={(e) => e.key === 'Enter' && addItem()}
              />
            </div>

            <div className="md:col-span-6">
              <label className="block text-xs font-medium mb-1">Quantity</label>
              <div className="relative">
                <Input
                  type="number"
                  inputMode="decimal"
                  placeholder="0"
                  value={newItem.quantity}
                  onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })}
                  onKeyDown={(e) => e.key === 'Enter' && addItem()}
                  className="pr-16"
                />
                <div className="absolute inset-y-0 right-1 flex items-center gap-1">
                  <Button type="button" size="icon" variant="ghost" className="h-7 w-7" onClick={() => bumpQtyLocal(-1)}>
                    <Minus className="h-3 w-3" />
                  </Button>
                  <Button type="button" size="icon" variant="ghost" className="h-7 w-7" onClick={() => bumpQtyLocal(1)}>
                    <Plus className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              <p className="mt-1 text-[11px] text-muted-foreground">Use ↑/↓ keys or the steppers.</p>
            </div>

            <div className="md:col-span-6">
              <label className="block text-xs font-medium mb-1">Unit</label>
              <Select value={newItem.unit} onValueChange={(val) => setNewItem({ ...newItem, unit: val })}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose unit" />
                </SelectTrigger>
                <SelectContent className="bg-background border-border">
                  {UNITS.map((u) => (
                    <SelectItem key={u} value={u}>
                      {u}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="md:col-span-6">
              <label className="block text-xs font-medium mb-1">Category</label>
              <Select value={newItem.category} onValueChange={(val) => setNewItem({ ...newItem, category: val })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent className="bg-background border-border">
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="md:col-span-6">
              <label className="block text-xs font-medium mb-1">Expiry (optional)</label>
              <div className="relative">
                <Input
                  type="date"
                  value={newItem.expiry}
                  onChange={(e) => setNewItem({ ...newItem, expiry: e.target.value })}
                />
                <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
              </div>
            </div>

            <div className="md:col-span-12 flex flex-col sm:flex-row sm:justify-end gap-2 pt-1">
              <Button type="button" variant="ghost" onClick={resetForm}>
                Clear
              </Button>
              <Button
                onClick={addItem}
                className="bg-gradient-primary border-0 sm:min-w-[160px]"
                disabled={busy}
              >
                <Plus className="h-4 w-4 mr-1" />
                {createItemMutation.isPending ? 'Adding...' : 'Add Item'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* list */}
      {inventory.length === 0 ? (
        <Card className="border-dashed border-muted rounded-2xl">
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
                  disabled={busy}
                >
                  + {q.name}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : filteredInventory.length === 0 ? (
        <Card className="border-dashed border-muted rounded-2xl">
          <CardContent className="p-6 text-center space-y-3">
            <p className="text-sm text-muted-foreground">
              No items match your current filters.
            </p>
            <Button variant="outline" onClick={clearFilters}>
              Clear Filters
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {/* Group by category only if no search/filters are active, otherwise show flat list */}
          {!hasActiveFilters ? (
            // Grouped by category
            Array.from(new Set(filteredInventory.map((it: any) => it.category || 'Other'))).map((category) => (
              <div key={category} className="space-y-2">
                <h4 className="font-medium text-sm text-accent">{category}</h4>
                <div className="space-y-2">
                  {filteredInventory
                    .filter((it: any) => (it.category || 'Other') === category)
                    .map((it: any) => {
                      const itemId = (it._id as string) || it.id?.toString() || '';
                      return (
                        <InventoryItemRow
                          key={itemId}
                          item={it}
                          busy={busy}
                          onInc={() => updateQuantity(itemId, 1)}
                          onDec={() => updateQuantity(itemId, -1)}
                          onDelete={() => removeItem(itemId)}
                        />
                      );
                    })}
                </div>
              </div>
            ))
          ) : (
            // Flat list when filters are active
            <div className="space-y-2">
              {filteredInventory.map((it: any) => {
                const itemId = (it._id as string) || it.id?.toString() || '';
                return (
                  <InventoryItemRow
                    key={itemId}
                    item={it}
                    busy={busy}
                    onInc={() => updateQuantity(itemId, 1)}
                    onDec={() => updateQuantity(itemId, -1)}
                    onDelete={() => removeItem(itemId)}
                  />
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Inventory Status - Modern Dashboard Style */}
      <Card className="relative overflow-hidden bg-gradient-to-br from-blue-50/80 via-white/70 to-purple-50/80 backdrop-blur-xl border border-white/40 rounded-3xl shadow-xl">
        {/* Animated background orbs */}
        <div className="absolute top-4 right-8 w-16 h-16 bg-gradient-to-br from-blue-300/20 to-cyan-300/20 rounded-full blur-lg animate-pulse"></div>
        <div className="absolute bottom-6 left-6 w-12 h-12 bg-gradient-to-br from-purple-300/20 to-pink-300/20 rounded-full blur-lg animate-pulse delay-1000"></div>
        
        <CardHeader className="relative z-10 pb-4">
          <CardTitle className="text-2xl font-bold bg-gradient-to-r from-gray-800 via-blue-700 to-purple-700 bg-clip-text text-transparent flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
              <Package className="h-4 w-4 text-white" />
            </div>
            Inventory Status
          </CardTitle>
        </CardHeader>

        <CardContent className="relative z-10 grid grid-cols-2 gap-8">
          <div className="text-center p-6 bg-white/50 backdrop-blur-sm rounded-2xl border border-white/20 hover:bg-white/70 transition-all duration-300 hover:scale-105">
            <div className="mb-3">
              <div className="w-12 h-12 mx-auto bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
                <Calendar className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="text-3xl font-bold bg-gradient-to-r from-amber-600 to-orange-600 bg-clip-text text-transparent">
              {expiringSoonCount}
            </div>
            <p className="text-sm font-medium text-gray-600 mt-1">Expiring Soon</p>
          </div>

          <div className="text-center p-6 bg-white/50 backdrop-blur-sm rounded-2xl border border-white/20 hover:bg-white/70 transition-all duration-300 hover:scale-105">
            <div className="mb-3">
              <div className="w-12 h-12 mx-auto bg-gradient-to-br from-blue-400 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg">
                <Package className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
              {lowStockCount}
            </div>
            <p className="text-sm font-medium text-gray-600 mt-1">Running Low</p>
          </div>
        </CardContent>
      </Card>

    </div>
  );
};
