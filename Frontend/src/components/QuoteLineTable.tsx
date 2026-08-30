import React from 'react';
import { QuoteLineItem } from '@/services/api';
import { Badge } from '@/components/ui/badge';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ExternalLink,
  HelpCircle,
  PackageCheck
} from 'lucide-react';

interface QuoteLineTableProps {
  lines: QuoteLineItem[];
  storeName: string;
}

export const QuoteLineTable: React.FC<QuoteLineTableProps> = ({ lines, storeName }) => {
  if (!lines || lines.length === 0) {
    return (
      <div className="text-center py-6 text-xs text-muted-foreground italic border rounded-xl bg-muted/10">
        No quote lines generated for {storeName}.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-border/60 bg-card/60">
      <table className="w-full text-left text-xs">
        <thead className="bg-muted/40 border-b border-border/60 text-muted-foreground uppercase tracking-wider font-semibold text-[10px]">
          <tr>
            <th className="py-2.5 px-3">Product</th>
            <th className="py-2.5 px-3">Pack & Sizing</th>
            <th className="py-2.5 px-3">Quantity</th>
            <th className="py-2.5 px-3">Match Status</th>
            <th className="py-2.5 px-3 text-right">Unit Price</th>
            <th className="py-2.5 px-3 text-right">Total</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/40">
          {lines.map((line, idx) => {
            const isFound = line.packs_added > 0 && line.is_in_stock;

            return (
              <tr key={line.id || line.shopping_item_id || idx} className="hover:bg-muted/30 transition-colors">
                {/* Product Title, SKU, Brand */}
                <td className="py-2.5 px-3 max-w-xs">
                  <div className="font-medium text-foreground truncate">{line.product_title}</div>
                  <div className="flex items-center gap-2 text-[10px] text-muted-foreground mt-0.5">
                    {line.product_brand && <span>Brand: {line.product_brand}</span>}
                    {line.retailer_sku && line.retailer_sku !== 'NOT_FOUND' && (
                      <span className="font-mono">SKU: {line.retailer_sku}</span>
                    )}
                    {line.product_url && (
                      <a
                        href={line.product_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary hover:underline inline-flex items-center"
                      >
                        <ExternalLink className="w-2.5 h-2.5 ml-0.5" />
                      </a>
                    )}
                  </div>
                </td>

                {/* Pack Size */}
                <td className="py-2.5 px-3 text-muted-foreground">
                  {line.pack_size || line.unit_measure || '1 pack'}
                </td>

                {/* Quantity */}
                <td className="py-2.5 px-3">
                  <div className="font-medium text-foreground">
                    {line.packs_added} {line.packs_added === 1 ? 'pack' : 'packs'}
                  </div>
                  <div className="text-[10px] text-muted-foreground">
                    Req: {line.requested_quantity} {line.unit_measure}
                  </div>
                </td>

                {/* Match Status */}
                <td className="py-2.5 px-3">
                  {isFound ? (
                    line.is_exact_match ? (
                      <Badge className="text-[10px] px-1.5 py-0 bg-emerald-500/15 text-emerald-600 border-emerald-500/20 font-medium">
                        <CheckCircle2 className="w-2.5 h-2.5 mr-1" /> Exact Match
                      </Badge>
                    ) : (
                      <Badge className="text-[10px] px-1.5 py-0 bg-blue-500/15 text-blue-600 border-blue-500/20 font-medium">
                        <PackageCheck className="w-2.5 h-2.5 mr-1" /> Substituted
                      </Badge>
                    )
                  ) : (
                    <div className="space-y-0.5">
                      <Badge variant="destructive" className="text-[10px] px-1.5 py-0 font-medium">
                        <XCircle className="w-2.5 h-2.5 mr-1" /> Missing
                      </Badge>
                      {line.missing_reason && (
                        <div className="text-[10px] text-destructive/80 line-clamp-1">
                          {line.missing_reason}
                        </div>
                      )}
                    </div>
                  )}
                </td>

                {/* Unit Price */}
                <td className="py-2.5 px-3 text-right font-mono text-muted-foreground">
                  {line.unit_price_cents > 0 ? `$${(line.unit_price_cents / 100).toFixed(2)}` : '-'}
                </td>

                {/* Line Total */}
                <td className="py-2.5 px-3 text-right font-mono font-semibold text-foreground">
                  {line.line_total_cents > 0 ? `$${(line.line_total_cents / 100).toFixed(2)}` : '$0.00'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
