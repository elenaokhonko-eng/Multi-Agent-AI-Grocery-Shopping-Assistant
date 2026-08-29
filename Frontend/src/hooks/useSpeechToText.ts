import { useEffect, useRef, useState } from "react";

interface SpeechRecognitionAlternative {
  transcript: string;
}

interface SpeechRecognitionResult {
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
  length: number;
}

interface SpeechRecognitionResultList {
  [index: number]: SpeechRecognitionResult;
  length: number;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionInstance extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: (() => void) | null;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}

interface WindowWithSpeech extends Window {
  SpeechRecognition?: new () => SpeechRecognitionInstance;
  webkitSpeechRecognition?: new () => SpeechRecognitionInstance;
}

export function useSpeechToText(opts?: { lang?: string; continuous?: boolean }) {
  const { lang = "en-US", continuous = true } = opts || {};

  const [isSupported, setIsSupported] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [interim, setInterim] = useState("");
  const [finalText, setFinalText] = useState("");

  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const manualStopRef = useRef(false);

  useEffect(() => {
    const win = window as WindowWithSpeech;
    const SR = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (!SR) {
      setIsSupported(false);
      return;
    }

    const rec = new SR();
    rec.lang = lang;
    rec.continuous = continuous;
    rec.interimResults = true;

    rec.onstart = () => setIsRecording(true);

    rec.onresult = (e: SpeechRecognitionEvent) => {
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

    rec.onerror = (e: { error: string }) => {
      if (e?.error !== "no-speech") console.warn("Speech error:", e);
    };

    rec.onend = () => {
      setIsRecording(false);
      setInterim("");
      if (!manualStopRef.current) {
        try { rec.start(); } catch (err) { console.debug("Speech restart skipped", err); }
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
    try { recognitionRef.current.start(); } catch (err) { console.debug("Speech start skipped", err); }
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
