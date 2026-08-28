import React, { useState, useEffect } from 'react';
import { 
  api, 
  ShoppingList, 
  ShoppingListItem, 
  ComparisonRunDetails, 
  StoreQuoteSummary, 
  ApprovalResponse, 
  OrderConfirmationResponse 
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
  TrendingDown
} from 'lucide-react';

export const CanonicalShoppingJourney: React.FC = () => {
  const { toast } = useToast();

  // 1. Shopping List State
  const [activeList, setActiveList] = useState<ShoppingList | null>(null);
  const [items, setItems] = useState<ShoppingListItem[]>([]);
  const [newItemName, setNewItemName] = useState('');
  const [newItemQty, setNewItemQty] = useState(1);
  const [newItemCategory, setNewItemCategory] = useState('Produce');
  const [isLoadingList, setIsLoadingList] = useState(true);

  // 2. Comparison & Agent Stepper State
  const [isComparing, setIsComparing] = useState(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [storeStates, setStoreStates] = useState<Record<string, { state: string; progress: number; detail?: string }>>({
    fairprice: { state: 'QUEUED', progress: 0 },
    shengsiong: { state: 'QUEUED', progress: 0 },
    littlefarms: { state: 'QUEUED', progress: 0 },
    redmart: { state: 'QUEUED', progress: 0 },
  });
  const [runDetails, setRunDetails] = useState<ComparisonRunDetails | null>(null);

  // 3. Approval & Order Confirmation State
  const [selectedQuote, setSelectedQuote] = useState<StoreQuoteSummary | null>(null);
  const [isApproving, setIsApproving] = useState(false);
  const [approvalData, setApprovalData] = useState<ApprovalResponse | null>(null);
  const [confirmedOrder, setConfirmedOrder] = useState<OrderConfirmationResponse | null>(null);

  // Load canonical shopping list on mount
  useEffect(() => {
    loadDefaultList();
  }, []);

  const loadDefaultList = async () => {
    try {
      setIsLoadingList(true);
      const lists = await api.getShoppingLists();
      if (lists.length > 0) {
        const fullList = await api.getShoppingList(lists[0].id);
        setActiveList(fullList);
        setItems(fullList.items || []);
      }
    } catch (err: any) {
      toast({
        title: 'Failed to load list',
        description: err.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoadingList(false);
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeList || !newItemName.trim()) return;

    try {
      const added = await api.addItemToList(activeList.id, {
        name: newItemName.trim(),
        category: newItemCategory,
        desired_quantity: Number(newItemQty) || 1,
        must_have: true,
        is_enabled: true,
      });
      setItems([...items, added]);
      setNewItemName('');
      setNewItemQty(1);
      toast({ title: 'Item added', description: `${added.name} added to your basket.` });
    } catch (err: any) {
      toast({ title: 'Error adding item', description: err.message, variant: 'destructive' });
    }
  };

  const handleToggleMustHave = async (item: ShoppingListItem) => {
    if (!activeList) return;
    try {
      const updated = await api.updateItem(activeList.id, item.id, { must_have: !item.must_have });
      setItems(items.map((i) => (i.id === item.id ? { ...i, must_have: updated.must_have } : i)));
    } catch (err: any) {
      toast({ title: 'Update failed', description: err.message, variant: 'destructive' });
    }
  };

  const handleDeleteItem = async (itemId: string) => {
    if (!activeList) return;
    try {
      await api.deleteItem(activeList.id, itemId);
      setItems(items.filter((i) => i.id !== itemId));
      toast({ title: 'Item removed' });
    } catch (err: any) {
      toast({ title: 'Delete failed', description: err.message, variant: 'destructive' });
    }
  };

  // Launch live multi-agent comparison
  const handleStartComparison = async () => {
    if (!activeList || items.length === 0) return;

    setIsComparing(true);
    setRunDetails(null);
    setSelectedQuote(null);
    setConfirmedOrder(null);

    // Reset stepper states
    setStoreStates({
      fairprice: { state: 'SESSION_CHECK', progress: 10, detail: 'Checking session' },
      shengsiong: { state: 'SESSION_CHECK', progress: 10, detail: 'Checking session' },
      littlefarms: { state: 'SESSION_CHECK', progress: 10, detail: 'Checking session' },
      redmart: { state: 'SESSION_CHECK', progress: 10, detail: 'Checking session' },
    });

    try {
      const init = await api.startComparisonRun(activeList.id);
      setCurrentRunId(init.run_id);

      // Connect SSE Stream
      const sseUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/comparison-runs/${init.run_id}/events`;
      const eventSource = new EventSource(sseUrl);

      eventSource.addEventListener('store_state', (evt: any) => {
        try {
          const payload = JSON.parse(evt.data);
          setStoreStates((prev) => ({
            ...prev,
            [payload.retailer_id]: {
              state: payload.state,
              progress: payload.progress_pct,
              detail: payload.detail,
            },
          }));
        } catch (_) {}
      });

      // Poll final quotes after agents finish
      setTimeout(async () => {
        try {
          const details = await api.getComparisonRun(init.run_id);
          setRunDetails(details);
          setIsComparing(false);
          eventSource.close();
        } catch (_) {}
      }, 2500);

    } catch (err: any) {
      setIsComparing(false);
      toast({ title: 'Comparison failed', description: err.message, variant: 'destructive' });
    }
  };

  // Approval flow (Strict Server Boundary)
  const handleApproveQuote = async (quote: StoreQuoteSummary) => {
    setSelectedQuote(quote);
    setIsApproving(true);
    try {
      const appResp = await api.approveQuote(quote.quote_id, quote.selected_delivery_slot_id || 'default_slot');
      setApprovalData(appResp);
    } catch (err: any) {
      toast({ title: 'Approval initiation failed', description: err.message, variant: 'destructive' });
    } finally {
      setIsApproving(false);
    }
  };

  const handleFinalSubmit = async () => {
    if (!approvalData) return;
    setIsApproving(true);
    try {
      const receipt = await api.submitApproval(approvalData.approval_id, approvalData.approval_token);
      setConfirmedOrder(receipt);
      toast({ title: 'Order placed successfully!', description: `Confirmation: ${receipt.retailer_order_id}` });
    } catch (err: any) {
      toast({
        title: 'Safety Stop / Submission Error',
        description: err.message,
        variant: 'destructive',
      });
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div className="container mx-auto p-4 max-w-6xl space-y-8 animate-fade-in text-slate-900 dark:text-slate-100">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <ShoppingCart className="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
            Singapore Multi-Store Grocery Optimizer
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Compare live carts across FairPrice, Sheng Siong, Little Farms & RedMart with deterministic price integrity.
          </p>
        </div>
        <Badge variant="outline" className="text-xs px-3 py-1 font-mono border-emerald-500/40 text-emerald-600 dark:text-emerald-400 self-start md:self-auto">
          <ShieldCheck className="h-3.5 w-3.5 mr-1" />
          Server-Authoritative Contract Active
        </Badge>
      </div>

      {/* Confirmed Order Banner */}
      {confirmedOrder && (
        <Card className="bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 shadow-md">
          <CardHeader>
            <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400 font-semibold text-lg">
              <CheckCircle2 className="h-6 w-6" />
              Verified Order Confirmation
            </div>
            <CardDescription className="text-emerald-800 dark:text-emerald-300">
              Your real supermarket order has been locked and confirmed.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <span className="text-slate-500 text-xs uppercase block">Retailer</span>
                <strong className="capitalize">{confirmedOrder.retailer_id}</strong>
              </div>
              <div>
                <span className="text-slate-500 text-xs uppercase block">Order Confirmation #</span>
                <span className="font-mono font-bold text-emerald-700 dark:text-emerald-400">{confirmedOrder.retailer_order_id}</span>
              </div>
              <div>
                <span className="text-slate-500 text-xs uppercase block">Total Paid (GST incl)</span>
                <strong>S${(confirmedOrder.confirmed_total_cents / 100).toFixed(2)}</strong>
              </div>
              <div>
                <span className="text-slate-500 text-xs uppercase block">Delivery Slot</span>
                <span>{confirmedOrder.confirmed_delivery_slot}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 1: Fixed Shopping List Editor */}
      <Card className="shadow-sm border-slate-200 dark:border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-xl flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-xs">1</span>
              Canonical Shopping List
            </CardTitle>
            <CardDescription>
              {activeList?.name || 'Regular Weekly Groceries'} — Version {activeList?.version || 1}
            </CardDescription>
          </div>
          <Button 
            onClick={handleStartComparison} 
            disabled={isComparing || items.length === 0}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium shadow"
          >
            {isComparing ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Agents Running...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Run Multi-Store Agents
              </>
            )}
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          
          {/* Quick Add Item Bar */}
          <form onSubmit={handleAddItem} className="flex flex-col sm:flex-row gap-2">
            <Input 
              placeholder="e.g. Fresh Lemons, Meiji Milk 2L, Eggs 10s..."
              value={newItemName}
              onChange={(e) => setNewItemName(e.target.value)}
              className="flex-1"
            />
            <Input 
              type="number"
              min="1"
              max="20"
              value={newItemQty}
              onChange={(e) => setNewItemQty(Number(e.target.value))}
              className="w-20"
            />
            <Button type="submit" variant="secondary" className="flex items-center gap-1">
              <Plus className="h-4 w-4" /> Add Item
            </Button>
          </form>

          {/* Items Table */}
          <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="p-3 text-left">Item Name</th>
                  <th className="p-3 text-center">Quantity</th>
                  <th className="p-3 text-center">Must Have</th>
                  <th className="p-3 text-center">Preferred Brand</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/20">
                    <td className="p-3 font-medium">{item.name}</td>
                    <td className="p-3 text-center">{item.desired_quantity} {item.unit_measure}</td>
                    <td className="p-3 text-center">
                      <Badge 
                        onClick={() => handleToggleMustHave(item)}
                        variant={item.must_have ? 'default' : 'secondary'}
                        className="cursor-pointer text-xs"
                      >
                        {item.must_have ? 'Required' : 'Optional'}
                      </Badge>
                    </td>
                    <td className="p-3 text-center text-slate-500 text-xs">
                      {item.preferred_brands?.join(', ') || 'Any brand'}
                    </td>
                    <td className="p-3 text-right">
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        onClick={() => handleDeleteItem(item.id)}
                        className="text-red-500 hover:text-red-700 h-8 w-8 p-0"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Step 2: Live Agent Stepper (Real-time SSE Status) */}
      {(isComparing || runDetails) && (
        <Card className="shadow-sm border-slate-200 dark:border-slate-800">
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-xs">2</span>
              Live Agent Execution Stepper
            </CardTitle>
            <CardDescription>
              Four parallel browser workers building and verifying authoritative retailer baskets.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(storeStates).map(([retailer, data]) => (
                <div key={retailer} className="p-4 border rounded-xl bg-slate-50/50 dark:bg-slate-900/30 border-slate-200 dark:border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold capitalize flex items-center gap-1.5">
                      <Store className="h-4 w-4 text-slate-500" />
                      {retailer}
                    </span>
                    <Badge variant={data.state === 'QUOTED' ? 'default' : 'outline'} className="text-xs uppercase font-mono">
                      {data.state}
                    </Badge>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div 
                      className="bg-emerald-500 h-1.5 transition-all duration-300"
                      style={{ width: `${data.progress || (data.state === 'QUOTED' ? 100 : 30)}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-500 truncate">{data.detail || 'Processing catalog...'}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Comparison Cards & Quotes */}
      {runDetails && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-xs">3</span>
              Live Price Comparison & Basket Audit
            </h2>
            {runDetails.cheapest_complete_store && (
              <Badge className="bg-emerald-600 text-white px-3 py-1 font-semibold flex items-center gap-1">
                <TrendingDown className="h-4 w-4" />
                Cheapest Eligible: {runDetails.cheapest_complete_store.toUpperCase()}
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {runDetails.quotes.map((quote) => {
              const isWinner = quote.retailer_id === runDetails.cheapest_complete_store;
              return (
                <Card 
                  key={quote.quote_id} 
                  className={`flex flex-col justify-between transition-all border-2 ${
                    isWinner ? 'border-emerald-500 shadow-md bg-emerald-50/20 dark:bg-emerald-950/10' : 'border-slate-200 dark:border-slate-800'
                  }`}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="capitalize text-lg">{quote.retailer_id}</CardTitle>
                      {isWinner && <Badge className="bg-emerald-500 text-white text-xs">Best Match</Badge>}
                    </div>
                    <div className="text-3xl font-extrabold text-slate-900 dark:text-white mt-2">
                      S${(quote.gross_total_cents / 100).toFixed(2)}
                    </div>
                    <span className="text-xs text-slate-500">
                      Net: S${(quote.derived_net_cents / 100).toFixed(2)} + 9% GST S${(quote.gst_cents / 100).toFixed(2)}
                    </span>
                  </CardHeader>
                  <CardContent className="space-y-3 text-xs">
                    <div className="border-t pt-2 space-y-1">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Items Subtotal:</span>
                        <span>S${(quote.subtotal_cents / 100).toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Delivery Fee:</span>
                        <span>{quote.delivery_fee_cents === 0 ? 'FREE' : `S$${(quote.delivery_fee_cents / 100).toFixed(2)}`}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Status:</span>
                        <span className="font-semibold text-emerald-600">{quote.is_complete ? 'Complete Basket (100%)' : 'Partial Basket'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Slot:</span>
                        <span className="truncate max-w-[140px]">{quote.selected_delivery_slot_window || 'Tomorrow AM'}</span>
                      </div>
                    </div>

                    {/* Matched Line Items Mini List */}
                    <div className="border-t pt-2 max-h-32 overflow-y-auto space-y-1">
                      {quote.lines.map((line, idx) => (
                        <div key={idx} className="flex justify-between items-center text-[11px]">
                          <span className="truncate max-w-[120px]" title={line.product_title}>{line.product_title}</span>
                          <span className="font-mono">S${(line.line_total_cents / 100).toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                  <CardFooter className="pt-2 border-t">
                    <Button 
                      onClick={() => handleApproveQuote(quote)}
                      disabled={isApproving}
                      className="w-full bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:text-slate-900 font-medium"
                    >
                      Approve & Lock Cart
                    </Button>
                  </CardFooter>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Step 4: Strict Server Approval Confirmation Modal */}
      {selectedQuote && approvalData && (
        <Card className="border-2 border-slate-900 dark:border-slate-100 shadow-xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b pb-3">
            <div>
              <h3 className="text-lg font-bold">Final Approval Gate — {selectedQuote.retailer_id.toUpperCase()}</h3>
              <p className="text-xs text-slate-500">Token ID: {approvalData.approval_token}</p>
            </div>
            <Badge variant="outline" className="font-mono text-xs">Expires in 15 mins</Badge>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm bg-slate-50 dark:bg-slate-900/50 p-4 rounded-lg">
            <div>
              <span className="text-xs text-slate-500 uppercase block">Total to be Paid</span>
              <strong className="text-xl">S${(selectedQuote.gross_total_cents / 100).toFixed(2)}</strong>
            </div>
            <div>
              <span className="text-xs text-slate-500 uppercase block">Fingerprint Hash</span>
              <span className="font-mono text-[10px] truncate block max-w-[150px]">{selectedQuote.cart_fingerprint}</span>
            </div>
            <div>
              <span className="text-xs text-slate-500 uppercase block">Delivery Slot</span>
              <span>{selectedQuote.selected_delivery_slot_window || 'Standard Window'}</span>
            </div>
          </div>

          <p className="text-xs text-slate-500">
            By clicking "Confirm Final Purchase", the agent will perform a pre-submission cart diff check and execute the transaction with live retailer authorization.
          </p>

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => setSelectedQuote(null)}>Cancel</Button>
            <Button 
              onClick={handleFinalSubmit}
              disabled={isApproving}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
            >
              {isApproving ? 'Submitting with Lock...' : 'Confirm Final Purchase'}
            </Button>
          </div>
        </Card>
      )}

    </div>
  );
};

export default CanonicalShoppingJourney;
