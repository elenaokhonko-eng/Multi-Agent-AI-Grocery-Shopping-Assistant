import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Send, Bot, User, Loader2, MessageSquare, X, Minimize2 } from "lucide-react";

type Role = "user" | "assistant";

interface ChatMessage {
  role: Role;
  content: string;
  ts: number; // unix ms
}

interface RagResponse {
  reply: string;
  query?: string;
}

// If you have a dev proxy: keep this as "/api/rag/chat".
// If not, use "http://127.0.0.1:3004/api/rag/chat".
const API_URL = "http://127.0.0.1:3004/api/rag/chat";

const fmtTime = (ts: number) =>
  new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const fmtDate = (ts: number) =>
  new Date(ts).toLocaleDateString([], { month: "long", day: "numeric" });

const sameDay = (a: number, b: number) => {
  const da = new Date(a);
  const db = new Date(b);
  return (
    da.getFullYear() === db.getFullYear() &&
    da.getMonth() === db.getMonth() &&
    da.getDate() === db.getDate()
  );
};

const FloatingChat = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hi 👋, I'm your AI shopping assistant. Ask me anything!",
      ts: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
    }
  }, [messages, loading, isOpen]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text, ts: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }), // backend expects { message }
      });

      const data: RagResponse = await res.json();

      const botMsg: ChatMessage = {
        role: "assistant",
        content: data?.reply ?? "Hmm, I couldn't get a response right now.",
        ts: Date.now(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ Error: could not connect to chatbot service.",
          ts: Date.now(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Send on Enter; Shift+Enter is ignored here (using Input)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <Button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-gradient-primary shadow-lg hover:shadow-xl transition-all duration-300 z-50"
          size="icon"
        >
          <MessageSquare className="h-6 w-6" />
        </Button>
      )}

      {/* Floating Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[500px] z-50">
          <Card className="shadow-xl border-0 h-full flex flex-col">
            {/* Header */}
            <CardHeader className="p-4 pb-2 border-b bg-gradient-primary text-white rounded-t-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bot className="h-5 w-5" />
                  <span className="font-semibold">AI Assistant</span>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-white hover:bg-white/20"
                    onClick={() => setIsOpen(false)}
                  >
                    <Minimize2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-white hover:bg-white/20"
                    onClick={() => setIsOpen(false)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent className="p-0 flex-1 flex flex-col">
              {/* Scrollable message list */}
              <div
                ref={listRef}
                className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-muted/20 to-background max-h-[350px]"
              >
                {messages.map((m, i) => {
                  const showDate = i === 0 || !sameDay(messages[i - 1].ts, m.ts);
                  const isUser = m.role === "user";

                  return (
                    <div key={i} className="space-y-2">
                      {showDate && (
                        <div className="relative flex items-center">
                          <div className="flex-1 h-px bg-border" />
                          <span className="mx-3 text-xs text-muted-foreground">
                            {fmtDate(m.ts)}
                          </span>
                          <div className="flex-1 h-px bg-border" />
                        </div>
                      )}

                      <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
                        {/* Left avatar (bot) */}
                        {!isUser && (
                          <div className="mr-2">
                            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center border border-border">
                              <Bot className="h-4 w-4 text-primary" />
                            </div>
                          </div>
                        )}

                        {/* Bubble + time */}
                        <div className={`max-w-[75%] ${isUser ? "items-end text-right" : ""}`}>
                          <div
                            className={`rounded-2xl px-3 py-2 border whitespace-pre-wrap shadow-sm text-sm ${
                              isUser
                                ? "bg-primary text-primary-foreground border-primary/30"
                                : "bg-white text-foreground border-border"
                            }`}
                          >
                            {m.content}
                          </div>

                          <div className={`mt-1 text-xs text-muted-foreground ${isUser ? "" : "pl-1"}`}>
                            {fmtTime(m.ts)}
                          </div>
                        </div>

                        {/* Right avatar (user) */}
                        {isUser && (
                          <div className="ml-2">
                            <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center border border-border">
                              <User className="h-4 w-4 text-muted-foreground" />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}

                {loading && (
                  <div className="flex items-center gap-2 text-muted-foreground text-sm">
                    <Loader2 className="h-4 w-4 animate-spin" /> thinking…
                  </div>
                )}
              </div>

              {/* Sticky composer */}
              <div className="border-t bg-background p-3">
                <div className="flex gap-2">
                  <Input
                    placeholder="Write a message…"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="text-sm"
                  />
                  <Button
                    onClick={sendMessage}
                    disabled={loading || !input.trim()}
                    className="bg-gradient-primary"
                    size="sm"
                  >
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
};

export default FloatingChat;
