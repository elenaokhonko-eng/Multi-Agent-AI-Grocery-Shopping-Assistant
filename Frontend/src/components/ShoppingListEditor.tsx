import React, { useState } from 'react';
import { ShoppingListItem, api } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import {
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  Sparkles,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  Tag,
  ShieldAlert,
  Layers,
  Scale
} from 'lucide-react';

const CATEGORIES = [
  'Produce',
  'Dairy & Chilled',
  'Beverages',
  'Bakery',
  'Meat & Seafood',
  'Pantry',
  'Frozen',
  'Household',
  'Snacks',
  'Personal Care'
];

const CANONICAL_UNITS = [
  'g',
  'kg',
  'ml',
  'l',
  'pack',
  'can',
  'bottle',
  'bunch',
  'piece',
  'box',
  'bag'
];

const SUBSTITUTION_POLICIES = [
  { value: 'EXACT_ONLY', label: 'Exact SKU / Brand Only' },
  { value: 'SAME_BRAND_ANY_SIZE', label: 'Same Brand (Any Size)' },
  { value: 'ANY_BRAND_SAME_PACK_SIZE', label: 'Any Brand (Same Pack Size)' },
  { value: 'ANY_BRAND_SIMILAR_PRICE', label: 'Any Brand (Similar Price)' },
  { value: 'CHEAPEST_IN_CATEGORY', label: 'Cheapest in Category' },
];

interface ShoppingListEditorProps {
  listId: string;
  listName: string;
  listVersion: number;
  items: ShoppingListItem[];
  onItemsChange: (items: ShoppingListItem[]) => void;
  disabled?: boolean;
}

export const ShoppingListEditor: React.FC<ShoppingListEditorProps> = ({
  listId,
  listName,
  listVersion,
  items,
  onItemsChange,
  disabled = false,
}) => {
  const { toast } = useToast();

  // Add Item State
  const [showAddForm, setShowAddForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newCategory, setNewCategory] = useState('Produce');
  const [newQuantity, setNewQuantity] = useState(1);
  const [newUnit, setNewUnit] = useState('pack');
  const [newMustHave, setNewMustHave] = useState(true);
  const [newSubPolicy, setNewSubPolicy] = useState('EXACT_ONLY');
  const [newMinPack, setNewMinPack] = useState('');
  const [newMaxPack, setNewMaxPack] = useState('');
  const [newBrands, setNewBrands] = useState('');
  const [newExclusions, setNewExclusions] = useState('');
  const [newPinnedFp, setNewPinnedFp] = useState('');
  const [newPinnedSs, setNewPinnedSs] = useState('');
  const [newPinnedLf, setNewPinnedLf] = useState('');
  const [newPinnedRm, setNewPinnedRm] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Edit Item State
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editFormData, setEditFormData] = useState<Partial<ShoppingListItem>>({});
  const [expandedItemId, setExpandedItemId] = useState<string | null>(null);

  const resetAddForm = () => {
    setNewName('');
    setNewCategory('Produce');
    setNewQuantity(1);
    setNewUnit('pack');
    setNewMustHave(true);
    setNewSubPolicy('EXACT_ONLY');
    setNewMinPack('');
    setNewMaxPack('');
    setNewBrands('');
    setNewExclusions('');
    setNewPinnedFp('');
    setNewPinnedSs('');
    setNewPinnedLf('');
    setNewPinnedRm('');
    setShowAddForm(false);
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || isSubmitting || disabled) return;

    try {
      setIsSubmitting(true);
      const pinned_skus: Record<string, string> = {};
      if (newPinnedFp.trim()) pinned_skus['fairprice'] = newPinnedFp.trim();
      if (newPinnedSs.trim()) pinned_skus['shengsiong'] = newPinnedSs.trim();
      if (newPinnedLf.trim()) pinned_skus['littlefarms'] = newPinnedLf.trim();
      if (newPinnedRm.trim()) pinned_skus['redmart'] = newPinnedRm.trim();

      const preferred_brands = newBrands
        .split(',')
        .map((b) => b.trim())
        .filter(Boolean);

      const exclusions = newExclusions
        .split(',')
        .map((x) => x.trim())
        .filter(Boolean);

      const created = await api.addItem(listId, {
        name: newName.trim(),
        category: newCategory,
        desired_quantity: Number(newQuantity) || 1,
        unit_measure: newUnit,
        min_pack_size: newMinPack.trim() || undefined,
        max_pack_size: newMaxPack.trim() || undefined,
        must_have: newMustHave,
        is_enabled: true,
        substitution_policy: newSubPolicy,
        preferred_brands,
        exclusions,
        pinned_skus,
      });

      onItemsChange([...items, created]);
      resetAddForm();
      toast({
        title: 'Item added',
        description: `Added "${created.name}" to shopping list.`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to add item';
      toast({
        title: 'Error adding item',
        description: msg,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const startEdit = (item: ShoppingListItem) => {
    setEditingItemId(item.id);
    setEditFormData({
      name: item.name,
      category: item.category,
      desired_quantity: item.desired_quantity,
      unit_measure: item.unit_measure,
      must_have: item.must_have,
      is_enabled: item.is_enabled,
      min_pack_size: item.min_pack_size || '',
      max_pack_size: item.max_pack_size || '',
      substitution_policy: item.substitution_policy,
      preferred_brands: item.preferred_brands || [],
      exclusions: item.exclusions || [],
      pinned_skus: item.pinned_skus || {},
    });
  };

  const cancelEdit = () => {
    setEditingItemId(null);
    setEditFormData({});
  };

  const saveEdit = async (itemId: string) => {
    if (disabled) return;
    try {
      const updated = await api.updateItem(listId, itemId, editFormData);
      onItemsChange(items.map((it) => (it.id === itemId ? updated : it)));
      setEditingItemId(null);
      setEditFormData({});
      toast({
        title: 'Item updated',
        description: `Updated "${updated.name}".`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update item';
      toast({
        title: 'Error updating item',
        description: msg,
        variant: 'destructive',
      });
    }
  };

  const handleDeleteItem = async (itemId: string, itemName: string) => {
    if (disabled) return;
    try {
      await api.deleteItem(listId, itemId);
      onItemsChange(items.filter((it) => it.id !== itemId));
      toast({
        title: 'Item removed',
        description: `Removed "${itemName}" from shopping list.`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete item';
      toast({
        title: 'Error deleting item',
        description: msg,
        variant: 'destructive',
      });
    }
  };

  const handleToggleEnabled = async (item: ShoppingListItem) => {
    if (disabled) return;
    try {
      const updated = await api.updateItem(listId, item.id, {
        is_enabled: !item.is_enabled,
      });
      onItemsChange(items.map((it) => (it.id === item.id ? updated : it)));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to toggle item';
      toast({
        title: 'Error toggling item',
        description: msg,
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Stats Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-card/60 backdrop-blur-md border rounded-2xl shadow-sm">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold tracking-tight text-foreground">{listName}</h2>
            <Badge variant="outline" className="text-xs font-semibold px-2 py-0.5 bg-primary/5 text-primary border-primary/20">
              v{listVersion} Snapshot Ready
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            {items.length} items configured ({items.filter((i) => i.is_enabled).length} enabled, {items.filter((i) => i.must_have && i.is_enabled).length} required)
          </p>
        </div>

        <Button
          onClick={() => setShowAddForm(!showAddForm)}
          disabled={disabled}
          className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-md transition-all duration-200"
        >
          {showAddForm ? <X className="w-4 h-4 mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
          {showAddForm ? 'Close Add Form' : 'Add Item'}
        </Button>
      </div>

      {/* Add Item Panel */}
      {showAddForm && (
        <Card className="border-primary/30 shadow-lg bg-card/90 backdrop-blur-md animate-in fade-in slide-in-from-top-4 duration-200">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              Add Item with Multi-Store Matching Rules
            </CardTitle>
            <CardDescription>
              Configure canonical unit, brand constraints, pack bounds, and exact pinned SKUs.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddItem} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
                {/* Item Name */}
                <div className="sm:col-span-6 space-y-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Product Name *</label>
                  <Input
                    placeholder="e.g. Fresh Milk, Lemons, Sparkling Water"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    required
                    className="bg-background"
                  />
                </div>

                {/* Category */}
                <div className="sm:col-span-3 space-y-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Desired Quantity */}
                <div className="sm:col-span-1 space-y-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Qty *</label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={newQuantity}
                    onChange={(e) => setNewQuantity(parseFloat(e.target.value) || 1)}
                    required
                    className="bg-background"
                  />
                </div>

                {/* Canonical Unit */}
                <div className="sm:col-span-2 space-y-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Unit</label>
                  <select
                    value={newUnit}
                    onChange={(e) => setNewUnit(e.target.value)}
                    className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {CANONICAL_UNITS.map((u) => (
                      <option key={u} value={u}>
                        {u}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Advanced Matching Controls */}
              <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 pt-2 border-t border-border/40">
                <div className="sm:col-span-4 space-y-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Substitution Policy</label>
                  <select
                    value={newSubPolicy}
                    onChange={(e) => setNewSubPolicy(e.target.value)}
                    className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {SUBSTITUTION_POLICIES.map((p) => (
                      <option key={p.value} value={p.value}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="sm:col-span-4 space-y-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Min / Max Pack Size</label>
                  <div className="grid grid-cols-2 gap-2">
                    <Input
                      placeholder="Min (e.g. 500g)"
                      value={newMinPack}
                      onChange={(e) => setNewMinPack(e.target.value)}
                      className="bg-background text-xs"
                    />
                    <Input
                      placeholder="Max (e.g. 2L)"
                      value={newMaxPack}
                      onChange={(e) => setNewMaxPack(e.target.value)}
                      className="bg-background text-xs"
                    />
                  </div>
                </div>

                <div className="sm:col-span-4 flex items-center gap-6 pt-5">
                  <label className="flex items-center gap-2 cursor-pointer text-sm font-medium">
                    <input
                      type="checkbox"
                      checked={newMustHave}
                      onChange={(e) => setNewMustHave(e.target.checked)}
                      className="w-4 h-4 rounded border-primary text-primary focus:ring-primary"
                    />
                    <span>Must-Have Item</span>
                  </label>
                </div>
              </div>

              {/* Brands & Exclusions */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Preferred Brands (comma-separated)</label>
                  <Input
                    placeholder="e.g. Meiji, Farmhouse, Marigold"
                    value={newBrands}
                    onChange={(e) => setNewBrands(e.target.value)}
                    className="bg-background text-sm"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Exclusions (comma-separated tokens)</label>
                  <Input
                    placeholder="e.g. low-fat, chocolate, powder"
                    value={newExclusions}
                    onChange={(e) => setNewExclusions(e.target.value)}
                    className="bg-background text-sm"
                  />
                </div>
              </div>

              {/* Pinned SKUs per Retailer */}
              <div className="space-y-2 pt-2 border-t border-border/40">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  <Tag className="w-3.5 h-3.5" />
                  Exact Pinned Store SKUs (Overrides AI Search)
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <Input
                    placeholder="FairPrice SKU"
                    value={newPinnedFp}
                    onChange={(e) => setNewPinnedFp(e.target.value)}
                    className="bg-background text-xs"
                  />
                  <Input
                    placeholder="Sheng Siong SKU"
                    value={newPinnedSs}
                    onChange={(e) => setNewPinnedSs(e.target.value)}
                    className="bg-background text-xs"
                  />
                  <Input
                    placeholder="Little Farms SKU"
                    value={newPinnedLf}
                    onChange={(e) => setNewPinnedLf(e.target.value)}
                    className="bg-background text-xs"
                  />
                  <Input
                    placeholder="RedMart SKU"
                    value={newPinnedRm}
                    onChange={(e) => setNewPinnedRm(e.target.value)}
                    className="bg-background text-xs"
                  />
                </div>
              </div>

              {/* Form Action Buttons */}
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="ghost" onClick={resetAddForm} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting || !newName.trim()} className="bg-primary text-primary-foreground">
                  {isSubmitting ? 'Adding...' : 'Save Item to List'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Items List Table & Cards */}
      <div className="space-y-3">
        {items.length === 0 ? (
          <div className="text-center py-12 border border-dashed rounded-2xl bg-card/40">
            <Layers className="w-12 h-12 mx-auto text-muted-foreground/40 mb-3" />
            <h3 className="text-base font-semibold text-foreground">No Items in Shopping List</h3>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto mt-1">
              Add your grocery staples above to start comparing authoritative real-time prices across Singapore stores.
            </p>
          </div>
        ) : (
          items.map((item) => {
            const isEditing = editingItemId === item.id;
            const isExpanded = expandedItemId === item.id;

            return (
              <div
                key={item.id}
                className={`transition-all duration-200 border rounded-xl overflow-hidden bg-card/70 backdrop-blur-sm ${
                  !item.is_enabled ? 'opacity-60 bg-muted/20 border-border/30' : 'border-border/60 hover:border-primary/40 shadow-sm'
                }`}
              >
                {/* Main Item Row */}
                <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  {/* Left Column: Checkbox, Name, Badges */}
                  <div className="flex items-center gap-3.5 flex-1 min-w-0">
                    <input
                      type="checkbox"
                      checked={item.is_enabled}
                      onChange={() => handleToggleEnabled(item)}
                      disabled={disabled}
                      className="w-4 h-4 rounded border-primary text-primary focus:ring-primary cursor-pointer"
                      title={item.is_enabled ? 'Disable item from comparison' : 'Enable item'}
                    />

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`font-semibold text-sm sm:text-base truncate ${!item.is_enabled ? 'line-through text-muted-foreground' : 'text-foreground'}`}>
                          {item.name}
                        </span>

                        <Badge variant="secondary" className="text-xs px-2 py-0">
                          {item.desired_quantity} {item.unit_measure}
                        </Badge>

                        {item.category && (
                          <Badge variant="outline" className="text-xs px-2 py-0 border-border/60 text-muted-foreground">
                            {item.category}
                          </Badge>
                        )}

                        {item.must_have ? (
                          <Badge className="text-xs px-2 py-0 bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/20 font-medium">
                            Must-Have
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-xs px-2 py-0 text-muted-foreground">
                            Optional
                          </Badge>
                        )}

                        {Object.keys(item.pinned_skus || {}).length > 0 && (
                          <Badge className="text-xs px-2 py-0 bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                            Pinned SKUs ({Object.keys(item.pinned_skus).length})
                          </Badge>
                        )}
                      </div>

                      {/* Sub-details (Brands, Exclusions, Bounds) */}
                      <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1 flex-wrap">
                        {item.preferred_brands?.length > 0 && (
                          <span>Brands: {item.preferred_brands.join(', ')}</span>
                        )}
                        {item.exclusions?.length > 0 && (
                          <span className="text-destructive/80">Exclude: {item.exclusions.join(', ')}</span>
                        )}
                        {(item.min_pack_size || item.max_pack_size) && (
                          <span>
                            Pack: {item.min_pack_size || '0'} - {item.max_pack_size || '∞'}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Actions */}
                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setExpandedItemId(isExpanded ? null : item.id)}
                      className="h-8 px-2 text-xs text-muted-foreground hover:text-foreground"
                    >
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5 mr-1" /> : <ChevronDown className="w-3.5 h-3.5 mr-1" />}
                      {isExpanded ? 'Hide Details' : 'Details'}
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => (isEditing ? cancelEdit() : startEdit(item))}
                      disabled={disabled}
                      className="h-8 px-2 text-xs hover:bg-primary/10 hover:text-primary"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteItem(item.id, item.name)}
                      disabled={disabled}
                      className="h-8 px-2 text-xs hover:bg-destructive/10 hover:text-destructive"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>

                {/* Expanded Details / Inline Edit Row */}
                {isEditing ? (
                  <div className="p-4 border-t bg-muted/30 space-y-4 animate-in fade-in duration-150">
                    <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
                      <div className="sm:col-span-5 space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">Product Name</label>
                        <Input
                          value={editFormData.name || ''}
                          onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                          className="bg-background text-sm"
                        />
                      </div>

                      <div className="sm:col-span-3 space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">Category</label>
                        <select
                          value={editFormData.category || 'Produce'}
                          onChange={(e) => setEditFormData({ ...editFormData, category: e.target.value })}
                          className="w-full h-10 px-2 rounded border bg-background text-sm"
                        >
                          {CATEGORIES.map((c) => (
                            <option key={c} value={c}>
                              {c}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="sm:col-span-2 space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">Qty</label>
                        <Input
                          type="number"
                          step="0.1"
                          min="0.1"
                          value={editFormData.desired_quantity ?? 1}
                          onChange={(e) => setEditFormData({ ...editFormData, desired_quantity: parseFloat(e.target.value) || 1 })}
                          className="bg-background text-sm"
                        />
                      </div>

                      <div className="sm:col-span-2 space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">Unit</label>
                        <select
                          value={editFormData.unit_measure || 'pack'}
                          onChange={(e) => setEditFormData({ ...editFormData, unit_measure: e.target.value })}
                          className="w-full h-10 px-2 rounded border bg-background text-sm"
                        >
                          {CANONICAL_UNITS.map((u) => (
                            <option key={u} value={u}>
                              {u}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 pt-2">
                      <div className="sm:col-span-4 space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">Substitution Policy</label>
                        <select
                          value={editFormData.substitution_policy || 'EXACT_ONLY'}
                          onChange={(e) => setEditFormData({ ...editFormData, substitution_policy: e.target.value })}
                          className="w-full h-10 px-2 rounded border bg-background text-sm"
                        >
                          {SUBSTITUTION_POLICIES.map((p) => (
                            <option key={p.value} value={p.value}>
                              {p.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="sm:col-span-4 space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">Min / Max Pack</label>
                        <div className="grid grid-cols-2 gap-2">
                          <Input
                            placeholder="Min (e.g. 500g)"
                            value={editFormData.min_pack_size || ''}
                            onChange={(e) => setEditFormData({ ...editFormData, min_pack_size: e.target.value })}
                            className="bg-background text-xs"
                          />
                          <Input
                            placeholder="Max (e.g. 2L)"
                            value={editFormData.max_pack_size || ''}
                            onChange={(e) => setEditFormData({ ...editFormData, max_pack_size: e.target.value })}
                            className="bg-background text-xs"
                          />
                        </div>
                      </div>

                      <div className="sm:col-span-4 flex items-center gap-4 pt-5">
                        <label className="flex items-center gap-2 cursor-pointer text-xs font-medium">
                          <input
                            type="checkbox"
                            checked={editFormData.must_have ?? true}
                            onChange={(e) => setEditFormData({ ...editFormData, must_have: e.target.checked })}
                            className="w-4 h-4 rounded border-primary text-primary focus:ring-primary"
                          />
                          <span>Must-Have</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer text-xs font-medium">
                          <input
                            type="checkbox"
                            checked={editFormData.is_enabled ?? true}
                            onChange={(e) => setEditFormData({ ...editFormData, is_enabled: e.target.checked })}
                            className="w-4 h-4 rounded border-primary text-primary focus:ring-primary"
                          />
                          <span>Enabled</span>
                        </label>
                      </div>
                    </div>

                    <div className="flex justify-end gap-2 pt-2">
                      <Button variant="ghost" size="sm" onClick={cancelEdit}>
                        <X className="w-4 h-4 mr-1" /> Cancel
                      </Button>
                      <Button size="sm" onClick={() => saveEdit(item.id)} className="bg-primary text-primary-foreground">
                        <Check className="w-4 h-4 mr-1" /> Save Changes
                      </Button>
                    </div>
                  </div>
                ) : isExpanded ? (
                  <div className="p-4 border-t bg-muted/20 text-xs space-y-2 animate-in fade-in duration-150">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div>
                        <span className="font-semibold text-muted-foreground">Substitution:</span>{' '}
                        <span>{item.substitution_policy}</span>
                      </div>
                      <div>
                        <span className="font-semibold text-muted-foreground">Pack Range:</span>{' '}
                        <span>{item.min_pack_size || 'None'} - {item.max_pack_size || 'None'}</span>
                      </div>
                      <div>
                        <span className="font-semibold text-muted-foreground">Brands:</span>{' '}
                        <span>{item.preferred_brands?.join(', ') || 'Any'}</span>
                      </div>
                      <div>
                        <span className="font-semibold text-muted-foreground">Exclusions:</span>{' '}
                        <span>{item.exclusions?.join(', ') || 'None'}</span>
                      </div>
                    </div>

                    {Object.keys(item.pinned_skus || {}).length > 0 && (
                      <div className="pt-2 border-t border-border/30">
                        <span className="font-semibold text-muted-foreground">Pinned SKUs:</span>{' '}
                        {Object.entries(item.pinned_skus).map(([store, sku]) => (
                          <Badge key={store} variant="outline" className="mr-2 text-xs">
                            {store}: {sku}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
