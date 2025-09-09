import { useState } from 'react';
import { Plus, Minus, X, Package, Calendar } from 'lucide-react';
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
    <Card key={id} className="border-border/60 hover:shadow-sm transition-shadow rounded-2xl">
      <CardContent className="p-3">
        <div className="flex items-center justify-between gap-3">
          {/* left: name + meta */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h5 className="font-medium text-sm truncate">{item.name}</h5>
              {expired && <Badge variant="destructive" className="text-xs">Expired</Badge>}
              {!expired && soon && (
                <Badge className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200">
                  Soon
                </Badge>
              )}
              {!expired && !soon && low && (
                <Badge className="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  Low
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              {qty} {unit}
              {item.expiry && (
                <span className="ml-2">
                  • Exp: {new Date(item.expiry).toLocaleDateString()}
                  {typeof daysUntil(item.expiry) === 'number' && (
                    <span className="ml-1 text-[11px]">({daysUntil(item.expiry)}d)</span>
                  )}
                </span>
              )}
            </p>
          </div>

          {/* right: qty control + delete */}
          <div className="flex items-center gap-2 shrink-0">
            {/* segmented qty control */}
            <div className="flex items-center rounded-lg border bg-accent/5 overflow-hidden">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-7 w-7 rounded-none"
                onClick={onDec}
                disabled={busy || qty <= 0}
                aria-label="Decrease quantity"
              >
                <Minus className="h-3 w-3" />
              </Button>
              <div className="px-3 text-sm tabular-nums select-none">{qty}</div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-7 w-7 rounded-none"
                onClick={onInc}
                disabled={busy}
                aria-label="Increase quantity"
              >
                <Plus className="h-3 w-3" />
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

  const { data: inventory = [], isLoading, error } = useInventoryItems();
  const createItemMutation = useCreateInventoryItem();
  const deleteItemMutation = useDeleteInventoryItem();
  const updateQuantityMutation = useUpdateQuantity();

  const busy = createItemMutation.isPending || deleteItemMutation.isPending || updateQuantityMutation.isPending;

  const resetForm = () =>
    setNewItem({ name: '', quantity: '', unit: 'pieces', category: 'Other', expiry: '' });

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

      {/* form */}
      <Card className="border-accent/30 shadow-sm rounded-2xl">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg md:text-xl font-semibold tracking-tight">Add New Item</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
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
      ) : (
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
          ))}
        </div>
      )}

      {/* stats */}
      <Card className="bg-[#F2FBFD] rounded-3xl shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg md:text-xl font-semibold tracking-tight">
            Inventory Status
          </CardTitle>
        </CardHeader>

        <CardContent className="grid grid-cols-2 gap-6 text-center">
          <div className="space-y-1">
            <div className="text-2xl md:text-3xl font-bold leading-none">1</div>
            <p className="text-sm md:text-base text-muted-foreground">Expiring Soon</p>
          </div>

          <div className="space-y-1">
            <div className="text-2xl md:text-3xl font-bold leading-none">1</div>
            <p className="text-sm md:text-base text-muted-foreground">Running Low</p>
          </div>
        </CardContent>
      </Card>

    </div>
  );
};
