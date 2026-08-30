import React, { useState } from 'react';
import {
  StoreQuoteSummary,
  ApprovalResponse,
  OrderConfirmationResponse,
  api
} from '@/services/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import {
  ShieldCheck,
  Lock,
  CheckCircle2,
  AlertTriangle,
  Receipt,
  ExternalLink,
  RefreshCw,
  X
} from 'lucide-react';

interface ApprovalDialogProps {
  quote: StoreQuoteSummary;
  approval: ApprovalResponse | null;
  onClose: () => void;
  onOrderSuccess: (receipt: OrderConfirmationResponse) => void;
}

export const ApprovalDialog: React.FC<ApprovalDialogProps> = ({
  quote,
  approval,
  onClose,
  onOrderSuccess,
}) => {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  const handleSubmitOrder = async () => {
    if (!approval) return;

    try {
      setIsSubmitting(true);
      setSubmissionError(null);
      const receipt = await api.submitApproval(approval.approval_id, approval.approval_token);
      toast({
        title: 'Order Confirmed!',
        description: `Order ${receipt.retailer_order_id} placed successfully.`,
      });
      onOrderSuccess(receipt);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Submission failed';
      setSubmissionError(msg);
      toast({
        title: 'Submission Failed',
        description: msg,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-md flex items-center justify-center p-4">
      <Card className="w-full max-w-xl border border-primary/40 shadow-2xl bg-card rounded-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <CardHeader className="p-6 pb-4 border-b border-border/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <CardTitle className="text-lg font-bold text-foreground">
                  Lock & Authorize Order
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground">
                  Server-Authoritative Quote Approval
                </CardDescription>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0 rounded-full">
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="p-6 space-y-4">
          {/* Store & Price Header */}
          <div className="p-4 bg-muted/40 rounded-xl border border-border/40 flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Store & Basket</div>
              <div className="text-base font-bold text-foreground capitalize">{quote.retailer_id}</div>
              <div className="text-xs text-muted-foreground mt-0.5">
                Delivery Window: <span className="font-semibold text-foreground">{quote.selected_delivery_slot_window || 'Standard'}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Confirmed Total</div>
              <div className="text-2xl font-black text-foreground">
                ${(quote.gross_total_cents / 100).toFixed(2)}
              </div>
              <div className="text-[10px] text-muted-foreground">Includes GST</div>
            </div>
          </div>

          {/* Security & Fingerprint Info */}
          <div className="space-y-2 p-3.5 bg-background border border-border/60 rounded-xl text-xs">
            <div className="flex items-center gap-2 font-semibold text-foreground">
              <Lock className="w-4 h-4 text-emerald-600" />
              Cart Cryptographic Fingerprint Locked
            </div>
            <div className="font-mono text-[11px] text-muted-foreground break-all bg-muted/50 p-2 rounded-lg">
              {approval?.expected_fingerprint || quote.cart_fingerprint}
            </div>
            <p className="text-[11px] text-muted-foreground">
              If the retailer modifies prices, basket lines, or out-of-stock items before checkout completes, the transaction will automatically fail-closed with <code>REAPPROVAL_REQUIRED</code>.
            </p>
          </div>

          {/* Submission Error Banner */}
          {submissionError && (
            <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-xl text-xs text-destructive flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <div>
                <div className="font-semibold">Checkout Guard Notice</div>
                <div className="text-[11px] mt-0.5">{submissionError}</div>
              </div>
            </div>
          )}
        </CardContent>

        <CardFooter className="p-6 pt-2 border-t border-border/40 flex items-center justify-between gap-3 bg-muted/10">
          <Button variant="ghost" onClick={onClose} disabled={isSubmitting} className="text-xs">
            Cancel
          </Button>

          <Button
            onClick={handleSubmitOrder}
            disabled={isSubmitting || !approval}
            className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-6 shadow-md transition-all"
          >
            {isSubmitting ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Submitting Order...
              </>
            ) : (
              <>
                <ShieldCheck className="w-4 h-4 mr-2" /> Authorize & Submit Order
              </>
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};
