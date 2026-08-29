import React, { useState, useEffect, useCallback } from 'react';
import { 
  api, 
  ShoppingList, 
  ShoppingListItem, 
  ComparisonRunDetails, 
  StoreQuoteSummary, 
  ApprovalResponse, 
  OrderConfirmationResponse,
  DeliverySlotItem
} from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { 
  ShoppingCart, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Plus, 
  Trash2, 
  RefreshCw, 
  ShieldCheck, 
  Store, 
  ExternalLink,
  ChevronRight,
  TrendingDown,
  Truck,
  Check,
  AlertTriangle
} from 'lucide-react';

export const CanonicalShoppingJourney: React.FC = () => {
  const { toast } = useToast();

  // 1. Shopping List State
  const [activeList, setActiveList] = useState<ShoppingList | null>(null);
  const [items, setItems] = useState<ShoppingListItem[]>([]);
  const [newItemName, setNewItemName] = useState('');
  const [newItemQty, setNewItemQty] = useState(1);
  const [newItemUnit, setNewItemUnit] = useState('pack');
  const [newItemCategory, setNewItemCategory] = useState('Produce');
  const [isLoadingList, setIsLoadingList] = useState(true);

  // 2. Comparison & Agent Stepper State
  const [isComparing, setIsComparing] = useState(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [storeStates, setStoreStates] = useState<Record<string, { state: string; progress: number; detail?: string; resumeToken?: string }>>({
    fairprice: { state: 'QUEUED', progress: 0 },
    shengsiong: { state: 'QUEUED', progress: 0 },
    littlefarms: { state: 'QUEUED', progress: 0 },
    redmart: { state: 'QUEUED', progress: 0 },
  });
  const [runDetails, setRunDetails] = useState<ComparisonRunDetails | null>(null);
  const [availableSlots, setAvailableSlots] = useState<Record<string, DeliverySlotItem[]>>({});
  const [selectedSlotMap, setSelectedSlotMap] = useState<Record<string, string>>({});

  // 3. Approval & Order Confirmation State
  const [selectedQuote, setSelectedQuote] = useState<StoreQuoteSummary | null>(null);
  const [isApproving, setIsApproving] = useState(false);
  const [approvalData, setApprovalData] = useState<ApprovalResponse | null>(null);
  const [confirmedOrder, setConfirmedOrder] = useState<OrderConfirmationResponse | null>(null);

  const loadDefaultList = useCallback(async () => {
    try {
      setIsLoadingList(true);
      const lists = await api.getShoppingLists();
      if (lists.length > 0) {
        const fullList = await api.getShoppingList(lists[0].id);
        setActiveList(fullList);
        setItems(fullList.items || []);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      toast({
        title: 'Failed to load list',
        description: msg,
        variant: 'destructive',
      });
    } finally {
      setIsLoadingList(false);
    }
  }, [toast]);

  useEffect(() => {
    loadDefaultList();
  }, [loadDefaultList]);

  // Handle Item Addition
  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeList || !newItemName.trim()) return;

    try {
      const added = await api.addItem(activeList.id, {
        name: newItemName.trim(),
        category: newItemCategory,
        desired_quantity: newItemQty,
        unit_measure: newItemUnit,
        must_have: true,
        is_enabled: true,
        substitution_policy: 'SAME_BRAND_ONLY',
        preferred_brands: [],
        exclusions: [],
        pinned_skus: {},
      });
      setItems(prev => [...prev, added]);
      setNewItemName('');
      setNewItemQty(1);
      toast({ title: 'Item added', description: `${added.name} added to your list.` });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to add item';
      toast({ title: 'Error adding item', description: msg, variant: 'destructive' });
    }
  };

  // Handle Item Toggle
  const handleToggleItem = async (itemId: string, currentEnabled: boolean) => {
    if (!activeList) return;
    try {
      const updated = await api.updateItem(activeList.id, itemId, { is_enabled: !currentEnabled });
      setItems(prev => prev.map(item => item.id === itemId ? updated : item));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update item';
      toast({ title: 'Error', description: msg, variant: 'destructive' });
    }
  };

  // Handle Item Delete
  const handleDeleteItem = async (itemId: string) => {
    if (!activeList) return;
    try {
      await api.deleteItem(activeList.id, itemId);
      setItems(prev => prev.filter(item => item.id !== itemId));
      toast({ title: 'Item removed' });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete item';
      toast({ title: 'Error', description: msg, variant: 'destructive' });
    }
  };

  // Start Multi-Agent Comparison Run
  const handleStartComparison = async () => {
    if (!activeList || items.filter(i => i.is_enabled).length === 0) {
      toast({ title: 'No active items', description: 'Enable at least one item to compare.', variant: 'destructive' });
      return;
    }

    try {
      setIsComparing(true);
      setRunDetails(null);
      setSelectedQuote(null);
      setApprovalData(null);
      setConfirmedOrder(null);
      setStoreStates({
        fairprice: { state: 'SESSION_CHECK', progress: 10, detail: 'Starting worker' },
        shengsiong: { state: 'SESSION_CHECK', progress: 10, detail: 'Starting worker' },
        littlefarms: { state: 'SESSION_CHECK', progress: 10, detail: 'Starting worker' },
        redmart: { state: 'SESSION_CHECK', progress: 10, detail: 'Starting worker' },
      });

      const runInit = await api.startComparison(activeList.id);
      setCurrentRunId(runInit.run_id);

      // Connect to Resilient Server-Sent Events (SSE) stream
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const eventSource = new EventSource(`${API_BASE}/comparison-runs/${runInit.run_id}/events`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.store_id) {
            setStoreStates(prev => ({
              ...prev,
              [data.store_id]: {
                state: data.to_state,
                progress: data.progress_pct,
                detail: data.detail,
                resumeToken: data.resume_token,
              }
            }));
          }
        } catch {
          // Keep stream alive
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
      };

      // Poll run results until completed
      const pollInterval = setInterval(async () => {
        try {
          const details = await api.getComparisonRun(runInit.run_id);
          if (details && details.quotes && details.quotes.length > 0) {
            setRunDetails(details);
            // Load delivery slots for all quotes
            for (const q of details.quotes) {
              api.getDeliverySlots(runInit.run_id, q.quote_id).then(slots => {
                setAvailableSlots(prev => ({ ...prev, [q.retailer_id]: slots }));
              }).catch(() => {});
            }
          }
          if (details.quotes.length >= 4 || !isComparing) {
            clearInterval(pollInterval);
            setIsComparing(false);
          }
        } catch {
          // Continue polling
        }
      }, 1200);

      setTimeout(() => {
        clearInterval(pollInterval);
        setIsComparing(false);
      }, 15000);

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to start comparison';
      toast({ title: 'Comparison Failed', description: msg, variant: 'destructive' });
      setIsComparing(false);
    }
  };

  // Select Delivery Slot
  const handleSlotSelect = async (quote: StoreQuoteSummary, slotId: string) => {
    if (!currentRunId) return;
    try {
      const updatedQuote = await api.selectDeliverySlot(currentRunId, quote.quote_id, slotId);
      setSelectedSlotMap(prev => ({ ...prev, [quote.retailer_id]: slotId }));
      setRunDetails(prev => {
        if (!prev) return null;
        return {
          ...prev,
          quotes: prev.quotes.map(q => q.quote_id === quote.quote_id ? updatedQuote : q)
        };
      });
      if (selectedQuote && selectedQuote.quote_id === quote.quote_id) {
        setSelectedQuote(updatedQuote);
      }
      toast({ title: 'Delivery Slot Selected', description: `Updated slot fee and total.` });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to select slot';
      toast({ title: 'Slot Selection Error', description: msg, variant: 'destructive' });
    }
  };

  // Open Approval Modal & Obtain Single-Use Token
  const handleOpenApproval = async (quote: StoreQuoteSummary) => {
    try {
      setIsApproving(true);
      const slotId = quote.selected_delivery_slot_id || 'default_slot';
      const approval = await api.createApproval(quote.quote_id, slotId);
      setApprovalData(approval);
      setSelectedQuote(quote);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to lock cart';
      toast({ title: 'Approval Lock Failed', description: msg, variant: 'destructive' });
    } finally {
      setIsApproving(false);
    }
  };

  // Final Order Confirmation Submission
  const handleConfirmOrder = async () => {
    if (!approvalData) return;
    try {
      setIsApproving(true);
      const confirmation = await api.submitApproval(approvalData.approval_id, approvalData.approval_token);
      setConfirmedOrder(confirmation);
      toast({
        title: 'Order Confirmed',
        description: `Retailer Order: ${confirmation.retailer_order_id}`,
      });
    } catch (err: unknown) {
      // 503 means live checkout is not yet wired — show a clear, honest message
      const isNotImplemented = err instanceof Error && err.message.includes('LIVE_CHECKOUT_NOT_IMPLEMENTED');
      const msg = isNotImplemented
        ? 'Live retailer checkout is not yet available. No order was placed. Your approval token is still valid.'
        : err instanceof Error ? err.message : 'Order submission failed';
      toast({ title: isNotImplemented ? 'Checkout Not Yet Available' : 'Submission Error', description: msg, variant: 'destructive' });
    } finally {
      setIsApproving(false);
    }
  };

  const getCheapestStore = () => {
    if (!runDetails || !runDetails.quotes || runDetails.quotes.length === 0) return null;
    const completeQuotes = runDetails.quotes.filter(q => q.is_complete);
    const pool = completeQuotes.length > 0 ? completeQuotes : runDetails.quotes;
    return [...pool].sort((a, b) => a.gross_total_cents - b.gross_total_cents)[0];
  };

  const cheapest = getCheapestStore();

  return (
    <div className="container mx-auto p-4 sm:p-6 max-w-7xl space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-gradient-to-r from-emerald-800 to-teal-900 text-white p-6 rounded-2xl shadow-xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-6 h-6 text-emerald-300" />
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Singapore Grocery Super-Assistant</h1>
          </div>
          <p className="text-emerald-100 text-sm">
            Live multi-agent market comparison across FairPrice, Sheng Siong, Little Farms & RedMart.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button 
            onClick={handleStartComparison} 
            disabled={isComparing || items.filter(i => i.is_enabled).length === 0}
            className="bg-emerald-400 hover:bg-emerald-300 text-emerald-950 font-bold px-6 py-6 rounded-xl shadow-lg transition-all transform hover:scale-105"
          >
            {isComparing ? (
              <>
                <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                Querying Supermarkets...
              </>
            ) : (
              <>
                <ShoppingCart className="w-5 h-5 mr-2" />
                Compare Store Prices
              </>
            )}
          </Button>
        </div>
      </div>

      {/* 1. Shopping List Management */}
      <Card className="border-emerald-100 dark:border-emerald-900/40 shadow-sm">
        <CardHeader className="pb-4">
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="text-xl flex items-center gap-2">
                <span>🛒 Shopping Basket</span>
                <Badge variant="outline" className="text-xs">
                  {items.filter(i => i.is_enabled).length} Active Items
                </Badge>
              </CardTitle>
              <CardDescription>
                Customize items, quantities, pack units, and exclusion filters before matching.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Add Item Form */}
          <form onSubmit={handleAddItem} className="flex flex-wrap gap-2 p-3 bg-muted/40 rounded-xl">
            <Input 
              placeholder="e.g. Fresh Lemons, Meiji Milk..." 
              value={newItemName}
              onChange={e => setNewItemName(e.target.value)}
              className="flex-1 min-w-[200px]"
            />
            <Input 
              type="number"
              min="1"
              max="99"
              value={newItemQty}
              onChange={e => setNewItemQty(parseInt(e.target.value) || 1)}
              className="w-20"
            />
            <select
              value={newItemUnit}
              onChange={e => setNewItemUnit(e.target.value)}
              className="px-3 py-2 border rounded-md text-sm bg-background"
            >
              <option value="pack">pack</option>
              <option value="pieces">pieces</option>
              <option value="L">L (litres)</option>
              <option value="kg">kg</option>
            </select>
            <select
              value={newItemCategory}
              onChange={e => setNewItemCategory(e.target.value)}
              className="px-3 py-2 border rounded-md text-sm bg-background"
            >
              <option value="Produce">Produce</option>
              <option value="Dairy & Chilled">Dairy & Chilled</option>
              <option value="Eggs">Eggs</option>
              <option value="Beverages">Beverages</option>
              <option value="Meat & Seafood">Meat & Seafood</option>
            </select>
            <Button type="submit" size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white">
              <Plus className="w-4 h-4 mr-1" /> Add
            </Button>
          </form>

          {/* Items Table */}
          {isLoadingList ? (
            <div className="text-center py-6 text-muted-foreground">Loading shopping list...</div>
          ) : (
            <div className="divide-y border rounded-xl overflow-hidden">
              {items.map(item => (
                <div key={item.id} className="flex items-center justify-between p-3.5 hover:bg-muted/20 transition-colors">
                  <div className="flex items-center gap-3">
                    <input 
                      type="checkbox"
                      checked={item.is_enabled}
                      onChange={() => handleToggleItem(item.id, item.is_enabled)}
                      className="w-4 h-4 text-emerald-600 rounded cursor-pointer"
                    />
                    <div>
                      <div className="font-semibold flex items-center gap-2">
                        <span className={item.is_enabled ? 'text-foreground' : 'line-through text-muted-foreground'}>
                          {item.name}
                        </span>
                        {item.must_have && <Badge variant="secondary" className="text-[10px]">Must-Have</Badge>}
                        {item.category && <Badge variant="outline" className="text-[10px]">{item.category}</Badge>}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Quantity: {item.desired_quantity} {item.unit_measure} 
                        {item.exclusions && item.exclusions.length > 0 && (
                          <span className="ml-2 text-rose-500">🚫 Exclude: {item.exclusions.join(', ')}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={() => handleDeleteItem(item.id)}
                    className="text-muted-foreground hover:text-rose-500"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 2. Live Agent Progression Stepper */}
      {isComparing && (
        <Card className="border-emerald-200 dark:border-emerald-800 bg-emerald-50/40 dark:bg-emerald-950/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <RefreshCw className="w-5 h-5 text-emerald-600 animate-spin" />
              Live Supermarket Scraping & Verification Pipeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(storeStates).map(([store, info]) => (
                <div key={store} className="p-4 border rounded-xl bg-background shadow-xs space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold capitalize">{store}</span>
                    <Badge variant={info.state === 'COMPLETED' ? 'default' : 'secondary'} className="text-[10px]">
                      {info.state}
                    </Badge>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                    <div 
                      className="bg-emerald-600 h-2 transition-all duration-300 rounded-full" 
                      style={{ width: `${info.progress}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground truncate">{info.detail || 'Working...'}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 3. Comparison Matrix & Store Quotes */}
      {runDetails && runDetails.quotes && runDetails.quotes.length > 0 && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Store className="w-6 h-6 text-emerald-600" />
              Store Price & Basket Comparison
            </h2>
            {cheapest && (
              <Badge className={cheapest.is_complete ? "bg-emerald-600 text-white px-3 py-1 text-sm font-semibold" : "bg-amber-600 text-white px-3 py-1 text-sm font-semibold"}>
                {cheapest.is_complete ? "🏆 Best Complete Option: " : "⚠️ Cheapest Incomplete Option: "}
                {cheapest.retailer_id.toUpperCase()} (${(cheapest.gross_total_cents / 100).toFixed(2)})
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6">
            {runDetails.quotes.map(quote => {
              const isBest = cheapest && cheapest.quote_id === quote.quote_id;
              const slots = availableSlots[quote.retailer_id] || [];

              return (
                <Card 
                  key={quote.quote_id} 
                  className={`flex flex-col justify-between border-2 transition-all shadow-md ${
                    isBest 
                      ? 'border-emerald-500 ring-2 ring-emerald-400/20 bg-emerald-50/10' 
                      : 'border-border'
                  }`}
                >
                  <CardHeader className="pb-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-xl font-bold capitalize flex items-center gap-2">
                          {quote.retailer_id}
                          {isBest && <Badge className="bg-amber-500 text-white text-[10px]">Cheapest</Badge>}
                        </CardTitle>
                        <CardDescription className="text-xs">
                          {quote.is_complete ? (
                            <span className="text-emerald-600 font-medium flex items-center gap-1 mt-0.5">
                              <CheckCircle2 className="w-3.5 h-3.5" /> All Items Matched ({quote.lines.filter(l => l.is_in_stock).length}/{quote.lines.length})
                            </span>
                          ) : (
                            <span className="text-rose-500 font-medium flex items-center gap-1 mt-0.5">
                              <AlertCircle className="w-3.5 h-3.5" /> {quote.missing_must_have_count} Missing Items ({quote.lines.filter(l => l.is_in_stock).length}/{quote.lines.length} Matched)
                            </span>
                          )}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    {/* Financial Breakdown */}
                    <div className="bg-muted/40 p-3.5 rounded-xl space-y-1.5 text-xs">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Basket Subtotal:</span>
                        <span className="font-semibold">${(quote.subtotal_cents / 100).toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Delivery Fee:</span>
                        <span>
                          {quote.delivery_fee_cents === 0 ? (
                            <span className="text-emerald-600 font-bold">FREE</span>
                          ) : (
                            `$${(quote.delivery_fee_cents / 100).toFixed(2)}`
                          )}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Service & Bag Fees:</span>
                        <span>${((quote.service_fee_cents + quote.bag_fee_cents) / 100).toFixed(2)}</span>
                      </div>
                      {quote.slot_fee_cents > 0 && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Peak Slot Surcharge:</span>
                          <span className="text-amber-600">+${(quote.slot_fee_cents / 100).toFixed(2)}</span>
                        </div>
                      )}
                      <div className="flex justify-between text-muted-foreground pt-1 border-t">
                        <span>GST (Inclusive 9%):</span>
                        <span>${(quote.gst_cents / 100).toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between text-base font-bold pt-1 border-t text-foreground">
                        <span>Grand Total:</span>
                        <span className="text-emerald-700 dark:text-emerald-400">
                          ${(quote.gross_total_cents / 100).toFixed(2)}
                        </span>
                      </div>
                    </div>

                    {/* Free Delivery Cutover Progress */}
                    {quote.free_delivery_threshold_cents && (
                      <div className="space-y-1">
                        <div className="flex justify-between text-[11px]">
                          <span className="text-muted-foreground flex items-center gap-1">
                            <Truck className="w-3 h-3" /> Free Delivery Cutover:
                          </span>
                          <span className="font-medium">
                            {quote.amount_needed_for_free_delivery_cents === 0 ? (
                              <span className="text-emerald-600 font-bold">Qualified! 🎉</span>
                            ) : (
                              `$${(quote.amount_needed_for_free_delivery_cents / 100).toFixed(2)} needed`
                            )}
                          </span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                          <div 
                            className="bg-emerald-500 h-1.5 rounded-full"
                            style={{ 
                              width: `${Math.min(100, (quote.subtotal_cents / quote.free_delivery_threshold_cents) * 100)}%` 
                            }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Delivery Slot Selection */}
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-muted-foreground" /> Choose Delivery Slot:
                      </label>
                      <select 
                        className="w-full text-xs p-2 border rounded-lg bg-background"
                        value={quote.selected_delivery_slot_id || ''}
                        onChange={e => handleSlotSelect(quote, e.target.value)}
                      >
                        {slots.map(s => (
                          <option key={s.slot_id} value={s.slot_id}>
                            {s.display_label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Item Lines Preview */}
                    <div className="space-y-2 border-t pt-2 max-h-48 overflow-y-auto pr-1">
                      {quote.lines.map(line => (
                        <div key={line.retailer_sku} className="text-xs p-2 rounded-lg bg-muted/20 flex justify-between items-start">
                          <div className="flex-1 pr-2">
                            <div className={`font-medium ${!line.is_in_stock ? 'line-through text-rose-500' : ''}`}>
                              {line.product_title}
                            </div>
                            <div className="text-[10px] text-muted-foreground">
                              {line.pack_size && <span>Pack: {line.pack_size} | </span>}
                              {line.unit_price_cents > 0 && <span>Unit: ${(line.unit_price_cents / 100).toFixed(2)}/{line.unit_measure || 'pk'} | </span>}
                              Qty: {line.packs_added} {line.unit_measure}
                              {line.missing_reason && (
                                <span className="text-rose-500 font-semibold block">⚠️ {line.missing_reason}</span>
                              )}
                            </div>
                          </div>
                          <div className="text-right">
                            <span className="font-semibold block">${(line.line_total_cents / 100).toFixed(2)}</span>
                            {line.product_url && (
                              <a 
                                href={line.product_url} 
                                target="_blank" 
                                rel="noreferrer" 
                                className="text-[10px] text-emerald-600 hover:underline flex items-center gap-0.5 justify-end"
                              >
                                View <ExternalLink className="w-2.5 h-2.5" />
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>

                  <CardFooter className="pt-2">
                    {/* Finding #8: Only allow approval of complete carts */}
                    {quote.is_complete ? (
                      <Button 
                        onClick={() => handleOpenApproval(quote)}
                        disabled={isApproving}
                        className="w-full font-bold bg-emerald-600 hover:bg-emerald-500 text-white"
                      >
                        <ShieldCheck className="w-4 h-4 mr-1.5" />
                        Lock &amp; Approve Cart
                      </Button>
                    ) : (
                      <div className="w-full text-xs text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/30 border border-amber-300 rounded-xl p-3 flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                        <span>
                          <strong>{quote.missing_must_have_count} must-have item{quote.missing_must_have_count !== 1 ? 's' : ''} missing</strong> — approval is disabled until all items are found or removed from the list.
                        </span>
                      </div>
                    )}
                  </CardFooter>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Approval Confirmation Modal */}
      {approvalData && selectedQuote && !confirmedOrder && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in">
          <Card className="max-w-lg w-full bg-background border-2 border-emerald-500 shadow-2xl rounded-2xl overflow-hidden">
            <CardHeader className="bg-emerald-800 text-white p-6">
              <CardTitle className="text-2xl flex items-center gap-2">
                <ShieldCheck className="w-6 h-6 text-emerald-300" />
                Cart Locked & Ready for Checkout
              </CardTitle>
              <CardDescription className="text-emerald-100">
                Authoritative quote locked for {selectedQuote.retailer_id.toUpperCase()}.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div className="bg-muted p-4 rounded-xl space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Store:</span>
                  <span className="font-bold capitalize">{selectedQuote.retailer_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Delivery Slot:</span>
                  <span className="font-semibold">{selectedQuote.selected_delivery_slot_window || 'Standard Slot'}</span>
                </div>
                <div className="flex justify-between text-base font-bold border-t pt-2">
                  <span>Authoritative Total:</span>
                  <span className="text-emerald-600">${(selectedQuote.gross_total_cents / 100).toFixed(2)}</span>
                </div>
              </div>

              {/* Itemized Basket in Modal */}
              <div className="space-y-1.5 border rounded-xl p-3 bg-muted/20 max-h-40 overflow-y-auto">
                <span className="text-xs font-semibold text-muted-foreground block">Itemized Approved Basket:</span>
                {selectedQuote.lines.filter(l => l.is_in_stock).map(line => (
                  <div key={line.retailer_sku} className="flex justify-between text-xs py-1 border-b last:border-0">
                    <span className="truncate max-w-[240px]">{line.product_title} (x{line.packs_added})</span>
                    <span className="font-medium shrink-0">${(line.line_total_cents / 100).toFixed(2)}</span>
                  </div>
                ))}
              </div>

              {/* Finding #3: Inform user that live checkout is not yet wired */}
              <div className="p-3 bg-blue-50 dark:bg-blue-950/30 border border-blue-300 rounded-xl text-blue-800 dark:text-blue-200 text-xs flex gap-2">
                <span className="font-semibold">ℹ️ Development status:</span>
                <span>Live retailer checkout is not yet implemented. Clicking "Submit" will return a 503 and no order will be placed at any retailer.</span>
              </div>

              <div className="text-xs text-muted-foreground">
                Single-use Approval Token: <code className="bg-muted px-1.5 py-0.5 rounded">{approvalData.approval_token}</code>
              </div>
            </CardContent>
            <CardFooter className="p-6 bg-muted/20 border-t flex justify-end gap-3">
              <Button variant="outline" onClick={() => setApprovalData(null)}>
                Cancel
              </Button>
              <Button 
                onClick={handleConfirmOrder}
                disabled={isApproving}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-6"
                title="Live checkout not yet implemented — will return 503"
              >
                {isApproving ? 'Submitting to Retailer...' : 'Authorize & Submit Order'}
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}

      {/* 5. Verified Retailer Receipt Card */}
      {confirmedOrder && (
        <Card className="border-2 border-emerald-500 bg-emerald-50/20 shadow-xl rounded-2xl overflow-hidden animate-in zoom-in-95">
          <CardHeader className="bg-emerald-700 text-white p-6">
            <CardTitle className="text-2xl flex items-center gap-2">
              <Check className="w-7 h-7 text-emerald-300" />
              Verified Retailer Order Placed!
            </CardTitle>
            <CardDescription className="text-emerald-100">
              Your grocery order has been locked, verified and registered with {confirmedOrder.retailer_id.toUpperCase()}.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 bg-background border rounded-xl">
                <span className="text-xs text-muted-foreground block">Order Confirmation #</span>
                <span className="text-lg font-mono font-bold text-foreground">{confirmedOrder.retailer_order_id}</span>
              </div>
              <div className="p-4 bg-background border rounded-xl">
                <span className="text-xs text-muted-foreground block">Confirmed Amount</span>
                <span className="text-lg font-bold text-emerald-600">
                  ${(confirmedOrder.confirmed_total_cents / 100).toFixed(2)}
                </span>
              </div>
              <div className="p-4 bg-background border rounded-xl">
                <span className="text-xs text-muted-foreground block">Scheduled Window</span>
                <span className="text-sm font-semibold">{confirmedOrder.delivery_slot}</span>
              </div>
            </div>
          </CardContent>
          <CardFooter className="p-6 bg-muted/20 border-t flex justify-between items-center">
            <span className="text-xs text-muted-foreground">Order Timestamp: {new Date(confirmedOrder.placed_at).toLocaleString()}</span>
            <Button 
              onClick={() => {
                setConfirmedOrder(null);
                setApprovalData(null);
                setSelectedQuote(null);
              }}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
            >
              Start New Shopping Trip
            </Button>
          </CardFooter>
        </Card>
      )}
    </div>
  );
};

export default CanonicalShoppingJourney;
