import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { OrderConfirmationResponse, StoreQuoteSummary } from '@/services/api';
import {
  CheckCircle2,
  AlertTriangle,
  Clock,
  ExternalLink,
  Receipt,
  RotateCcw,
  ShieldCheck,
  Store,
  Truck,
  AlertCircle,
  HelpCircle,
  RefreshCw,
} from 'lucide-react';

export interface OrderStatusPanelProps {
  order?: OrderConfirmationResponse | null;
  quote?: StoreQuoteSummary | null;
  statusState?: 'IDLE' | 'SUBMITTING' | 'CONFIRMED' | 'SUBMISSION_UNCERTAIN' | 'FAILED' | 'REVALIDATION_FAILED';
  revalidationDiff?: {
    has_changes?: boolean;
    price_changed?: boolean;
    old_total_cents?: number;
    new_total_cents?: number;
    items_out_of_stock?: string[];
    detail?: string;
  } | null;
  onRetry?: () => void;
  onRequote?: () => void;
  onRefreshStatus?: () => void;
}

export const OrderStatusPanel: React.FC<OrderStatusPanelProps> = ({
  order,
  quote,
  statusState = 'IDLE',
  revalidationDiff,
  onRetry,
  onRequote,
  onRefreshStatus,
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    if (!onRefreshStatus) return;
    setIsRefreshing(true);
    try {
      await onRefreshStatus();
    } finally {
      setIsRefreshing(false);
    }
  };

  if (statusState === 'IDLE' && !order && !revalidationDiff) {
    return null;
  }

  // 1. REVALIDATION FAILED (Price changed or items out of stock)
  if (statusState === 'REVALIDATION_FAILED' || (revalidationDiff && revalidationDiff.has_changes)) {
    return (
      <Card className="border-amber-500/40 bg-amber-500/10 shadow-xl backdrop-blur-md rounded-2xl overflow-hidden animate-in fade-in duration-300">
        <CardHeader className="p-6 pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-600 dark:text-amber-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <CardTitle className="text-lg font-bold text-foreground">
                  Cart Changed Before Checkout
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground">
                  Live supermarket prices or inventory changed. Your pre-authorization was safely halted.
                </CardDescription>
              </div>
            </div>
            <Badge className="bg-amber-500/20 text-amber-600 dark:text-amber-400 border-amber-500/30 text-xs font-bold px-3 py-1">
              REVALIDATION_FAILED
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-6 pt-2 space-y-4">
          <div className="p-4 bg-background/70 rounded-xl border border-border/50 text-xs space-y-2">
            {revalidationDiff?.detail && (
              <p className="font-semibold text-foreground">{revalidationDiff.detail}</p>
            )}
            {revalidationDiff?.items_out_of_stock && revalidationDiff.items_out_of_stock.length > 0 && (
              <div className="text-destructive font-medium">
                Out of Stock SKUs: {revalidationDiff.items_out_of_stock.join(', ')}
              </div>
            )}
            {revalidationDiff?.price_changed && (
              <div className="flex items-center gap-4 text-xs font-medium">
                <div>
                  Approved Total: <span className="line-through text-muted-foreground">${((revalidationDiff.old_total_cents || 0) / 100).toFixed(2)}</span>
                </div>
                <div>
                  New Live Total: <span className="text-primary font-bold">${((revalidationDiff.new_total_cents || 0) / 100).toFixed(2)}</span>
                </div>
              </div>
            )}
          </div>
        </CardContent>
        <CardFooter className="p-6 pt-0 flex justify-end gap-3">
          {onRequote && (
            <Button
              onClick={onRequote}
              className="bg-primary text-primary-foreground font-semibold text-xs shadow-md"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1.5" /> Re-quote & Review Fresh Basket
            </Button>
          )}
        </CardFooter>
      </Card>
    );
  }

  // 2. SUBMISSION UNCERTAIN (Network drop or browser timeout during live submission)
  if (statusState === 'SUBMISSION_UNCERTAIN') {
    return (
      <Card className="border-orange-500/40 bg-orange-500/10 shadow-xl backdrop-blur-md rounded-2xl overflow-hidden animate-in fade-in duration-300">
        <CardHeader className="p-6 pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-orange-500/20 flex items-center justify-center text-orange-600 dark:text-orange-400">
                <HelpCircle className="w-6 h-6" />
              </div>
              <div>
                <CardTitle className="text-lg font-bold text-foreground">
                  Submission Status Uncertain
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground">
                  The order was dispatched, but the retailer's confirmation response timed out.
                </CardDescription>
              </div>
            </div>
            <Badge className="bg-orange-500/20 text-orange-600 dark:text-orange-400 border-orange-500/30 text-xs font-bold px-3 py-1">
              SUBMISSION_UNCERTAIN
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-6 pt-2 space-y-3 text-xs text-muted-foreground">
          <p>
            To prevent double-charging your card, automated retries have been paused. Please click below to reconcile order status with the retailer.
          </p>
        </CardContent>
        <CardFooter className="p-6 pt-0 flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            Reconcile Retailer State
          </Button>
          {onRetry && (
            <Button
              onClick={onRetry}
              className="bg-primary text-primary-foreground font-semibold text-xs shadow-md"
            >
              Retry Submission Check
            </Button>
          )}
        </CardFooter>
      </Card>
    );
  }

  // 3. SUBMITTING
  if (statusState === 'SUBMITTING') {
    return (
      <Card className="border-primary/40 bg-primary/5 shadow-lg rounded-2xl overflow-hidden animate-in fade-in duration-300">
        <CardContent className="p-6 flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
            <RefreshCw className="w-5 h-5 animate-spin" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-foreground">Executing Guarded Live Checkout</h4>
            <p className="text-xs text-muted-foreground">
              Revalidating authoritative cart and securing selected delivery window...
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // 4. CONFIRMED ORDER
  if (order || statusState === 'CONFIRMED') {
    return (
      <Card className="border-emerald-500/40 bg-emerald-500/10 shadow-xl backdrop-blur-md rounded-2xl overflow-hidden animate-in fade-in duration-300">
        <CardHeader className="p-6 pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold text-foreground">
                  Order Successfully Placed!
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground">
                  Authoritative Supermarket Transaction Receipt
                </CardDescription>
              </div>
            </div>
            <Badge className="bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-sm font-bold px-3 py-1">
              CONFIRMED
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-6 pt-2 space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-background/60 rounded-xl border border-border/40 text-xs">
            <div>
              <div className="text-muted-foreground uppercase text-[10px] font-semibold">Retailer Order ID</div>
              <div className="font-mono font-bold text-foreground text-sm mt-0.5">{order?.retailer_order_id || 'N/A'}</div>
            </div>
            <div>
              <div className="text-muted-foreground uppercase text-[10px] font-semibold">Store</div>
              <div className="font-bold text-foreground text-sm mt-0.5 capitalize">{order?.retailer_id || quote?.retailer_id}</div>
            </div>
            <div>
              <div className="text-muted-foreground uppercase text-[10px] font-semibold">Confirmed Total</div>
              <div className="font-bold text-foreground text-sm mt-0.5">
                ${(((order?.confirmed_total_cents ?? quote?.gross_total_cents) || 0) / 100).toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-muted-foreground uppercase text-[10px] font-semibold">Delivery Window</div>
              <div className="font-bold text-foreground text-sm mt-0.5">
                {order?.confirmed_delivery_slot || quote?.selected_delivery_slot_id || 'Standard'}
              </div>
            </div>
          </div>

          {order?.receipt_url && (
            <div className="flex justify-end">
              <a
                href={order.receipt_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center text-xs text-primary hover:underline font-semibold"
              >
                View Official Retailer Receipt <ExternalLink className="w-3.5 h-3.5 ml-1" />
              </a>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // 5. FAILED
  return (
    <Card className="border-destructive/40 bg-destructive/10 shadow-lg rounded-2xl overflow-hidden animate-in fade-in duration-300">
      <CardContent className="p-6 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-destructive/20 flex items-center justify-center text-destructive">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-foreground">Order Submission Failed</h4>
            <p className="text-xs text-muted-foreground">
              An error occurred during transaction processing.
            </p>
          </div>
        </div>
        {onRetry && (
          <Button variant="outline" onClick={onRetry} className="text-xs">
            Retry
          </Button>
        )}
      </CardContent>
    </Card>
  );
};
export default OrderStatusPanel;

