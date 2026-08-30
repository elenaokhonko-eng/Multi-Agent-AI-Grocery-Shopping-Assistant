import React, { useState } from 'react';
import { StoreQuoteSummary, DeliverySlotItem } from '@/services/api';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DeliverySlotSelector } from '@/components/DeliverySlotSelector';
import { QuoteLineTable } from '@/components/QuoteLineTable';
import {
  Store,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Truck,
  Sparkles,
  ExternalLink,
  Receipt,
  Layers
} from 'lucide-react';

interface StoreQuoteCardProps {
  quote: StoreQuoteSummary;
  isCheapestComplete?: boolean;
  slots?: DeliverySlotItem[];
  isSelectedForApproval?: boolean;
  onSelectSlot: (quoteId: string, slotId: string) => void;
  onApprove: (quote: StoreQuoteSummary) => void;
  disabled?: boolean;
}

const STORE_LABELS: Record<string, { name: string; brandColor: string; bgBadge: string }> = {
  fairprice: {
    name: 'NTUC FairPrice',
    brandColor: 'border-blue-500/40 text-blue-600 dark:text-blue-400',
    bgBadge: 'bg-blue-500/10'
  },
  shengsiong: {
    name: 'Sheng Siong',
    brandColor: 'border-emerald-500/40 text-emerald-600 dark:text-emerald-400',
    bgBadge: 'bg-emerald-500/10'
  },
  littlefarms: {
    name: 'Little Farms',
    brandColor: 'border-amber-500/40 text-amber-600 dark:text-amber-400',
    bgBadge: 'bg-amber-500/10'
  },
  redmart: {
    name: 'RedMart (Lazada)',
    brandColor: 'border-rose-500/40 text-rose-600 dark:text-rose-400',
    bgBadge: 'bg-rose-500/10'
  },
};

export const StoreQuoteCard: React.FC<StoreQuoteCardProps> = ({
  quote,
  isCheapestComplete = false,
  slots = [],
  isSelectedForApproval = false,
  onSelectSlot,
  onApprove,
  disabled = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const conf = STORE_LABELS[quote.retailer_id] || {
    name: quote.retailer_id,
    brandColor: 'border-border text-foreground',
    bgBadge: 'bg-muted'
  };

  const totalFeesCents =
    quote.delivery_fee_cents +
    quote.service_fee_cents +
    quote.bag_fee_cents +
    quote.slot_fee_cents;

  const hasFreeDelivery = quote.delivery_fee_cents === 0;

  return (
    <Card
      className={`border rounded-2xl transition-all duration-300 bg-card/85 backdrop-blur-md overflow-hidden ${
        isCheapestComplete
          ? 'border-emerald-500 shadow-lg shadow-emerald-500/10 ring-1 ring-emerald-500/30'
          : isSelectedForApproval
          ? 'border-primary shadow-md ring-1 ring-primary/40'
          : 'border-border/60 hover:border-primary/30 shadow-sm'
      }`}
    >
      {/* Top Highlight Banner for Best Complete Value */}
      {isCheapestComplete && (
        <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white px-4 py-1.5 text-xs font-semibold flex items-center justify-between shadow-sm">
          <span className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            Recommended Best Complete Value
          </span>
          <span className="text-[11px] opacity-90">All required items in stock</span>
        </div>
      )}

      <CardHeader className="p-5 pb-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Store className="w-5 h-5 text-muted-foreground" />
              <CardTitle className="text-lg font-bold text-foreground">{conf.name}</CardTitle>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Fingerprint: <span className="font-mono text-[10px]">{quote.cart_fingerprint?.slice(0, 16)}...</span>
            </p>
          </div>

          <div className="flex flex-col items-end gap-1">
            {quote.is_complete ? (
              <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-xs font-semibold px-2.5 py-0.5">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                100% In Stock
              </Badge>
            ) : (
              <Badge className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 text-xs font-semibold px-2.5 py-0.5">
                <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                Missing {quote.missing_must_have_count} Must-Have
              </Badge>
            )}
            <span className="text-[10px] text-muted-foreground">
              {quote.found_item_count} of {quote.requested_item_count} items matched
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-5 pt-2 space-y-4">
        {/* Main Price Headline */}
        <div className="p-4 rounded-xl bg-muted/30 border border-border/40 flex items-center justify-between">
          <div>
            <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Authoritative Gross Total</div>
            <div className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
              ${(quote.gross_total_cents / 100).toFixed(2)}
            </div>
          </div>
          <div className="text-right text-xs text-muted-foreground space-y-0.5">
            <div>Items Subtotal: ${(quote.subtotal_cents / 100).toFixed(2)}</div>
            <div>Total Fees: ${(totalFeesCents / 100).toFixed(2)}</div>
            <div className="text-[10px] text-muted-foreground/80">Includes ${(quote.gst_cents / 100).toFixed(2)} GST (9%)</div>
          </div>
        </div>

        {/* Free Delivery Status Bar */}
        {quote.free_delivery_threshold_cents ? (
          <div className="p-3 rounded-lg border border-border/40 bg-background/50 space-y-1.5 text-xs">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-muted-foreground font-medium">
                <Truck className="w-3.5 h-3.5 text-primary" />
                Free Delivery Threshold: ${(quote.free_delivery_threshold_cents / 100).toFixed(2)}
              </span>
              <span className="font-semibold text-foreground">
                {hasFreeDelivery
                  ? 'Qualified for Free Delivery!'
                  : `$${(quote.amount_needed_for_free_delivery_cents / 100).toFixed(2)} more needed`}
              </span>
            </div>
            <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                style={{
                  width: `${Math.min(
                    100,
                    Math.round((quote.subtotal_cents / quote.free_delivery_threshold_cents) * 100)
                  )}%`
                }}
              />
            </div>
          </div>
        ) : null}

        {/* Delivery Slot Selection */}
        {slots && slots.length > 0 && (
          <DeliverySlotSelector
            slots={slots}
            selectedSlotId={quote.selected_delivery_slot_id}
            onSelectSlot={(slotId) => onSelectSlot(quote.id || quote.quote_id || '', slotId)}
            disabled={disabled}
          />
        )}

        {/* Expandable Quote Lines Breakdown */}
        {isExpanded && (
          <div className="pt-2 animate-in fade-in slide-in-from-top-2 duration-200">
            <QuoteLineTable lines={quote.lines || []} storeName={conf.name} />
          </div>
        )}
      </CardContent>

      <CardFooter className="p-5 pt-0 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-border/30 bg-muted/10">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-xs text-muted-foreground hover:text-foreground w-full sm:w-auto"
        >
          {isExpanded ? <ChevronUp className="w-3.5 h-3.5 mr-1" /> : <ChevronDown className="w-3.5 h-3.5 mr-1" />}
          {isExpanded ? 'Hide Item Breakdown' : `View ${quote.lines?.length || 0} Item Breakdown`}
        </Button>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {quote.cart_url && (
            <a
              href={quote.cart_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center text-xs h-9 px-3 border rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
            >
              <ExternalLink className="w-3.5 h-3.5 mr-1" />
              View Cart
            </a>
          )}

          <Button
            onClick={() => onApprove(quote)}
            disabled={disabled || !quote.is_complete}
            className={`w-full sm:w-auto text-xs font-semibold shadow-md transition-all ${
              isCheapestComplete
                ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                : 'bg-primary hover:bg-primary/90 text-primary-foreground'
            }`}
          >
            <ShieldCheck className="w-4 h-4 mr-1.5" />
            {quote.is_complete ? 'Approve & Lock Cart' : 'Incomplete Cart Locked'}
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
};
