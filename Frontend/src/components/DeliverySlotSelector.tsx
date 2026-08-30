import React from 'react';
import { DeliverySlotItem } from '@/services/api';
import { Badge } from '@/components/ui/badge';
import { Clock, DollarSign } from 'lucide-react';

interface DeliverySlotSelectorProps {
  slots: DeliverySlotItem[];
  selectedSlotId?: string;
  onSelectSlot: (slotId: string) => void;
  disabled?: boolean;
}

export const DeliverySlotSelector: React.FC<DeliverySlotSelectorProps> = ({
  slots,
  selectedSlotId,
  onSelectSlot,
  disabled = false,
}) => {
  if (!slots || slots.length === 0) {
    return (
      <div className="text-xs text-muted-foreground italic py-1">
        Standard delivery slot automatically allocated.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        <Clock className="w-3.5 h-3.5" />
        <span>Select Delivery Window</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {slots.map((slot) => {
          const isSelected = selectedSlotId === slot.slot_id;

          return (
            <button
              key={slot.slot_id}
              type="button"
              disabled={disabled || !slot.is_available}
              onClick={() => onSelectSlot(slot.slot_id)}
              className={`flex items-center justify-between p-2.5 rounded-lg text-left text-xs transition-all border ${
                isSelected
                  ? 'border-primary bg-primary/10 text-foreground ring-1 ring-primary'
                  : 'border-border/60 bg-background/50 hover:bg-muted/50 text-muted-foreground'
              } ${!slot.is_available ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <div className="min-w-0 pr-2">
                <div className="font-semibold text-foreground truncate">{slot.display_label}</div>
                <div className="text-[10px] text-muted-foreground">
                  {new Date(slot.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -{' '}
                  {new Date(slot.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>

              <div className="flex items-center">
                {slot.fee_cents > 0 ? (
                  <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-border">
                    +${(slot.fee_cents / 100).toFixed(2)}
                  </Badge>
                ) : (
                  <Badge className="text-[10px] px-1.5 py-0 bg-emerald-500/15 text-emerald-600 border-emerald-500/20">
                    Free
                  </Badge>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
