import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  api,
  ShoppingList,
  ShoppingListItem,
  ComparisonRunDetails,
  StoreQuoteSummary,
  ApprovalResponse,
  OrderConfirmationResponse,
  DeliverySlotItem,
} from '@/services/api';
import { ShoppingListEditor } from '@/components/ShoppingListEditor';
import { StoreProgressGrid, StoreProgressInfo } from '@/components/StoreProgressGrid';
import { StoreQuoteCard } from '@/components/StoreQuoteCard';
import { ChallengeActionPanel } from '@/components/ChallengeActionPanel';
import { ApprovalDialog } from '@/components/ApprovalDialog';
import { OrderStatusPanel } from '@/components/OrderStatusPanel';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import {
  ShoppingCart,
  Sparkles,
  RefreshCw,
  Store,
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const DEFAULT_STORES = ['fairprice', 'shengsiong', 'littlefarms', 'redmart'];

export const CanonicalShoppingJourney: React.FC = () => {
  const { toast } = useToast();

  // 1. Shopping List State
  const [activeList, setActiveList] = useState<ShoppingList | null>(null);
  const [items, setItems] = useState<ShoppingListItem[]>([]);
  const [isLoadingList, setIsLoadingList] = useState(true);

  // 2. Comparison & Real-Time Stepper State
  const [isComparing, setIsComparing] = useState(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(() => {
    return localStorage.getItem('last_comparison_run_id') || null;
  });
  const [storeStates, setStoreStates] = useState<Record<string, StoreProgressInfo>>({
    fairprice: { state: 'QUEUED', progress: 0 },
    shengsiong: { state: 'QUEUED', progress: 0 },
    littlefarms: { state: 'QUEUED', progress: 0 },
    redmart: { state: 'QUEUED', progress: 0 },
  });
  const [runDetails, setRunDetails] = useState<ComparisonRunDetails | null>(null);
  const [activeChallenge, setActiveChallenge] = useState<{
    retailerId: string;
    actionType?: string;
    resumeToken?: string;
    message?: string;
  } | null>(null);

  // 3. Delivery Slots & Quote State
  const [availableSlots, setAvailableSlots] = useState<Record<string, DeliverySlotItem[]>>({});
  const [selectedQuote, setSelectedQuote] = useState<StoreQuoteSummary | null>(null);
  const [approvalData, setApprovalData] = useState<ApprovalResponse | null>(null);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [confirmedOrder, setConfirmedOrder] = useState<OrderConfirmationResponse | null>(null);
  const [orderStatusState, setOrderStatusState] = useState<'IDLE' | 'SUBMITTING' | 'CONFIRMED' | 'SUBMISSION_UNCERTAIN' | 'FAILED' | 'REVALIDATION_FAILED'>('IDLE');
  const [revalidationDiff, setRevalidationDiff] = useState<any | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);

  // Load Active Shopping List
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
      const msg = err instanceof Error ? err.message : 'Failed to load list';
      toast({
        title: 'Error loading shopping list',
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

  // Clean up EventSource on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // Poll for Run Details
  const pollRunDetails = useCallback(async (runId: string) => {
    try {
      const details = await api.getComparisonRun(runId);
      setRunDetails(details);

      if (['COMPLETED', 'COMPLETED_WITH_ERRORS', 'FAILED'].includes(details.status)) {
        setIsComparing(false);
      }
    } catch (err) {
      console.error('Error polling run details:', err);
    }
  }, []);

  // Recover active run on refresh
  useEffect(() => {
    if (currentRunId && !runDetails) {
      pollRunDetails(currentRunId);
    }
  }, [currentRunId, pollRunDetails, runDetails]);

  // Launch Comparison Run
  const handleStartComparison = async () => {
    if (!activeList || isComparing) return;

    try {
      setIsComparing(true);
      setConfirmedOrder(null);
      setApprovalData(null);
      setSelectedQuote(null);
      setActiveChallenge(null);
      setOrderStatusState('IDLE');
      setRevalidationDiff(null);

      // Reset store states
      const initialStates: Record<string, StoreProgressInfo> = {};
      DEFAULT_STORES.forEach((s) => {
        initialStates[s] = { state: 'QUEUED', progress: 0, detail: 'Initializing comparison' };
      });
      setStoreStates(initialStates);

      const runInit = await api.startComparison(activeList.id, DEFAULT_STORES);
      setCurrentRunId(runInit.run_id);
      localStorage.setItem('last_comparison_run_id', runInit.run_id);

      // Setup Server-Sent Events (SSE) Stream
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const sse = new EventSource(`${API_BASE_URL}/comparison-runs/${runInit.run_id}/events`);
      eventSourceRef.current = sse;

      sse.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const storeId = data.retailer_id;

          if (storeId) {
            setStoreStates((prev) => ({
              ...prev,
              [storeId]: {
                state: data.to_state || data.state,
                progress: data.progress_pct ?? prev[storeId]?.progress ?? 0,
                detail: data.message || prev[storeId]?.detail,
                actionType: data.action_type,
                resumeToken: data.resume_token,
              },
            }));

            if (data.to_state === 'USER_ACTION_REQUIRED' || data.state === 'USER_ACTION_REQUIRED') {
              setActiveChallenge({
                retailerId: storeId,
                actionType: data.action_type || 'LOGIN_REQUIRED',
                resumeToken: data.resume_token,
                message: data.message,
              });
            }
          }
        } catch (e) {
          console.error('Failed to parse SSE event:', e);
        }
      };

      sse.onerror = () => {
        sse.close();
      };

      // Interval Polling for run summary
      const interval = setInterval(() => {
        pollRunDetails(runInit.run_id);
      }, 1500);

      setTimeout(() => {
        clearInterval(interval);
        pollRunDetails(runInit.run_id);
      }, 30000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to start comparison';
      setIsComparing(false);
      toast({
        title: 'Comparison Failed',
        description: msg,
        variant: 'destructive',
      });
    }
  };

  // Handle Delivery Slot Selection
  const handleSelectSlot = async (quoteId: string, slotId: string) => {
    if (!currentRunId) return;
    try {
      const updatedQuote = await api.selectQuoteSlot(quoteId, slotId);
      if (runDetails) {
        setRunDetails({
          ...runDetails,
          quotes: runDetails.quotes.map((q) =>
            (q.id === quoteId || q.quote_id === quoteId) ? updatedQuote : q
          ),
        });
      }
      toast({
        title: 'Delivery slot updated',
        description: 'Quote fingerprint recalculated.',
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to select slot';
      toast({
        title: 'Error updating slot',
        description: msg,
        variant: 'destructive',
      });
    }
  };

  // Handle Quote Approval Trigger
  const handleOpenApproveDialog = async (quote: StoreQuoteSummary) => {
    try {
      setSelectedQuote(quote);
      const approval = await api.approveQuote(
        quote.id || quote.quote_id || '',
        quote.selected_delivery_slot_id || 'std_slot'
      );
      setApprovalData(approval);
      setShowApprovalDialog(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Approval failed';
      toast({
        title: 'Approval Error',
        description: msg,
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background/95 to-muted/20 text-foreground py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary shadow-sm">
                <ShoppingCart className="w-6 h-6" />
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
                Grocery Shopping Assistant
              </h1>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Multi-Agent Autonomous Supermarket Comparison & Server-Authoritative Purchasing
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button
              onClick={handleStartComparison}
              disabled={isComparing || isLoadingList || items.filter((i) => i.is_enabled).length === 0}
              className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-6 shadow-lg shadow-primary/20 transition-all duration-200"
            >
              {isComparing ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Comparing Stores...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" /> Launch 4-Store Comparison
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Challenge Action Panel (if any retailer requires login/action) */}
        {activeChallenge && currentRunId && (
          <ChallengeActionPanel
            runId={currentRunId}
            retailerId={activeChallenge.retailerId}
            actionType={activeChallenge.actionType}
            resumeToken={activeChallenge.resumeToken}
            message={activeChallenge.message}
            onResumeSuccess={() => {
              setActiveChallenge(null);
              if (currentRunId) pollRunDetails(currentRunId);
            }}
          />
        )}

        {/* Order Status & Recovery Panel */}
        <OrderStatusPanel
          order={confirmedOrder}
          quote={selectedQuote}
          statusState={orderStatusState}
          revalidationDiff={revalidationDiff}
          onRequote={() => {
            setOrderStatusState('IDLE');
            setRevalidationDiff(null);
            if (currentRunId) pollRunDetails(currentRunId);
          }}
          onRefreshStatus={() => {
            if (currentRunId) pollRunDetails(currentRunId);
          }}
        />

        {/* Store Comparison Progress Grid (Visible during or after run) */}
        {(isComparing || currentRunId) && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
                <Store className="w-5 h-5 text-primary" />
                Live Retailer Worker Stepper
              </h2>
              {runDetails?.status && (
                <Badge variant="outline" className="text-xs font-mono">
                  Run Status: {runDetails.status}
                </Badge>
              )}
            </div>
            <StoreProgressGrid
              storeStates={storeStates}
              onSolveChallenge={(retailerId, token) => {
                setActiveChallenge({
                  retailerId,
                  resumeToken: token,
                  actionType: 'LOGIN_REQUIRED',
                });
              }}
            />
          </div>
        )}

        {/* Store Quotes Section */}
        {runDetails && runDetails.quotes && runDetails.quotes.length > 0 && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h2 className="text-xl font-bold tracking-tight text-foreground">
                  Authoritative Store Quotes & Comparison
                </h2>
                <p className="text-xs text-muted-foreground">
                  Exact basket totals, delivery thresholds, and Singapore GST breakdown.
                </p>
              </div>
              {runDetails.cheapest_complete_store && (
                <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-xs font-semibold px-3 py-1 self-start sm:self-auto">
                  Lowest Price Complete Store: {runDetails.cheapest_complete_store.toUpperCase()}
                </Badge>
              )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {runDetails.quotes.map((quote) => (
                <StoreQuoteCard
                  key={quote.id || quote.quote_id || quote.retailer_id}
                  quote={quote}
                  isCheapestComplete={quote.retailer_id === runDetails.cheapest_complete_store}
                  slots={availableSlots[quote.retailer_id] || []}
                  isSelectedForApproval={selectedQuote?.retailer_id === quote.retailer_id}
                  onSelectSlot={handleSelectSlot}
                  onApprove={handleOpenApproveDialog}
                  disabled={isComparing}
                />
              ))}
            </div>
          </div>
        )}

        {/* Shopping List Editor (Editable Preloaded List) */}
        {activeList && (
          <ShoppingListEditor
            listId={activeList.id}
            listName={activeList.name}
            listVersion={activeList.version}
            items={items}
            onItemsChange={(newItems) => setItems(newItems)}
            disabled={isComparing}
          />
        )}

        {/* Approval Modal Dialog */}
        {showApprovalDialog && selectedQuote && (
          <ApprovalDialog
            quote={selectedQuote}
            approval={approvalData}
            onClose={() => setShowApprovalDialog(false)}
            onOrderSuccess={(receipt) => {
              setShowApprovalDialog(false);
              setConfirmedOrder(receipt);
              setOrderStatusState('CONFIRMED');
            }}
          />
        )}
      </div>
    </div>
  );
};

export default CanonicalShoppingJourney;
