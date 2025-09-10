import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Mic } from "lucide-react";

type Props = {
  levels: number[];
  active: boolean;
  interim?: string;
  onStop: () => void;
};

export default function VoiceCaptureUI({ levels, active, interim, onStop }: Props) {
  const [secs, setSecs] = useState(0);

  useEffect(() => {
    if (!active) {
      setSecs(0);
      return;
    }
    const id = setInterval(() => setSecs((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [active]);

  const time = useMemo(() => {
    const m = Math.floor(secs / 60).toString().padStart(2, "0");
    const s = (secs % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  }, [secs]);

  return (
    <div
      className="mt-2 ml-10 rounded-xl border bg-accent/5 px-3 py-2 flex items-center gap-3"
      aria-live="polite"
    >
      {/* pulsing mic */}
      <div className="relative">
        <div className="h-8 w-8 rounded-full grid place-items-center bg-red-500/90 text-white">
          <Mic className="h-4 w-4" />
        </div>
        <span className="absolute inset-0 rounded-full bg-red-500/40 animate-ping" />
      </div>

      {/* waveform */}
      <div className="flex-1">
        <div className="flex items-end gap-[3px] h-8">
          {levels.map((v, i) => {
            const h = Math.round(6 + v * 26); // bar height
            return (
              <div
                key={i}
                className="w-[3px] rounded-sm bg-red-500/70"
                style={{ height: `${h}px` }}
              />
            );
          })}
        </div>
        {interim && (
          <div className="text-xs mt-1 italic text-muted-foreground line-clamp-1">
            🎙️ {interim}
          </div>
        )}
      </div>

      <span className="text-xs tabular-nums text-muted-foreground">{time}</span>
      <Button size="sm" variant="ghost" onClick={onStop}>
        Stop
      </Button>
    </div>
  );
}
