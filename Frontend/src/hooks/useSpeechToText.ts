import { useEffect, useRef, useState } from "react";

export function useSpeechToText(opts?: { lang?: string; continuous?: boolean }) {
  const { lang = "en-US", continuous = true } = opts || {};

  const [isSupported, setIsSupported] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [interim, setInterim] = useState("");
  const [finalText, setFinalText] = useState("");

  const recognitionRef = useRef<any>(null);
  const manualStopRef = useRef(false);

  useEffect(() => {
    const SR =
      (window as any).webkitSpeechRecognition ||
      (window as any).SpeechRecognition;

    if (!SR) {
      setIsSupported(false);
      return;
    }

    const rec = new SR();
    rec.lang = lang;
    rec.continuous = continuous;
    rec.interimResults = true;

    rec.onstart = () => setIsRecording(true);

    rec.onresult = (e: any) => {
      let interimBuf = "";
      let finalBuf = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalBuf += t + " ";
        else interimBuf += t;
      }
      if (finalBuf) setFinalText(prev => (prev + finalBuf).trim());
      setInterim(interimBuf);
    };

    rec.onerror = (e: any) => {
      if (e?.error !== "no-speech") console.warn("Speech error:", e);
    };

    rec.onend = () => {
      setIsRecording(false);
      setInterim("");
      if (!manualStopRef.current) {
        try { rec.start(); } catch {}
      }
    };

    recognitionRef.current = rec;

    return () => {
      manualStopRef.current = true;
      recognitionRef.current?.stop?.();
      recognitionRef.current = null;
    };
  }, [lang, continuous]);

  const start = () => {
    if (!recognitionRef.current) return;
    manualStopRef.current = false;
    setFinalText("");
    setInterim("");
    try { recognitionRef.current.start(); } catch {}
  };

  const stop = () => {
    manualStopRef.current = true;
    recognitionRef.current?.stop?.();
  };

  const reset = () => {
    setFinalText("");
    setInterim("");
  };

  return { isSupported, isRecording, interim, finalText, start, stop, reset };
}
