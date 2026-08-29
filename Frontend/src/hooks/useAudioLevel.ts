import { useEffect, useRef, useState, useCallback } from "react";

interface WindowWithAudio extends Window {
  webkitAudioContext?: typeof AudioContext;
}

export function useAudioLevel(numBars: number = 24) {
  const [levels, setLevels] = useState<number[]>(() => Array(numBars).fill(0));
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataRef = useRef<Uint8Array | null>(null);
  const rafRef = useRef<number | null>(null);

  const cleanup = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
    analyserRef.current = null;
    dataRef.current = null;
    setIsActive(false);
    setLevels(Array(numBars).fill(0));
  }, [numBars]);

  const start = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const win = window as WindowWithAudio;
      const AudioCtxClass = window.AudioContext || win.webkitAudioContext;
      if (!AudioCtxClass) {
        throw new Error("AudioContext not supported");
      }
      const ctx: AudioContext = new AudioCtxClass();
      audioCtxRef.current = ctx;

      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.85;
      source.connect(analyser);

      analyserRef.current = analyser;
      dataRef.current = new Uint8Array(analyser.frequencyBinCount);

      setIsActive(true);

      const tick = () => {
        if (!analyserRef.current || !dataRef.current) return;
        analyserRef.current.getByteTimeDomainData(dataRef.current);
        const arr = dataRef.current;

        // compute RMS amplitude (0..1)
        let sum = 0;
        for (let i = 0; i < arr.length; i++) {
          const v = (arr[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / arr.length);
        const target = Math.min(1, rms * 3);

        setLevels((prev) =>
          prev.map((val, i) => {
            const eased = val + (target - val) * 0.5;
            return Math.max(0, Math.min(1, eased - i * 0.01));
          })
        );

        rafRef.current = requestAnimationFrame(tick);
      };
      tick();
    } catch (e: unknown) {
      const errName = e instanceof Error ? e.name : "mic-error";
      setError(errName);
      cleanup();
    }
  };

  const stop = () => cleanup();

  useEffect(() => () => cleanup(), [cleanup]);

  return { levels, isActive, error, start, stop };
}
