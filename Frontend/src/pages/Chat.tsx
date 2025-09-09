// Frontend/src/pages/Chat.tsx
import { useEffect, useRef, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Send, Bot, User, Loader2 } from "lucide-react";

type Role = "user" | "assistant";
interface ChatMessage {
  role: Role;
  content: string;
  ts: number; // unix ms
}

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

const Chat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi 👋, I’m your AI shopping assistant. Ask me anything!",
      ts: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text, ts: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [...messages, userMsg] }),
      });
      const data = await res.json();
      const botMsg: ChatMessage = {
        role: "assistant",
        content: data?.answer ?? "Hmm, I couldn’t get a response right now.",
        ts: Date.now(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ Error: could not connect to chatbot service.", ts: Date.now() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Send on Enter; Shift+Enter inserts a newline (future-proof if you switch to Textarea)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <div className="container mx-auto px-4 pt-6">
        <h1 className="text-2xl font-bold">AI Chat</h1>
      </div>

      {/* Chat card fills remaining height */}
      <div className="container mx-auto px-4 py-4 flex-1 flex">
        <Card className="shadow-soft border-0 flex-1 flex flex-col">
          <CardContent className="p-0 flex-1 flex flex-col">
            {/* Scrollable message list */}
            <div
              ref={listRef}
              className="flex-1 overflow-y-auto p-4 space-y-6 bg-gradient-to-b from-muted/40 to-background"
            >
              {messages.map((m, i) => {
                // date separators like the screenshot
                const showDate =
                  i === 0 || !sameDay(messages[i - 1].ts, m.ts);
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
                          <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center border border-border">
                            <Bot className="h-5 w-5 text-primary" />
                          </div>
                        </div>
                      )}

                      {/* Bubble + time */}
                      <div className={`max-w-[78%] ${isUser ? "items-end text-right" : ""}`}>
                        <div
                          className={`rounded-2xl px-4 py-2 border whitespace-pre-wrap shadow-sm ${
                            isUser
                              ? "bg-primary text-primary-foreground border-primary/30"
                              : "bg-white text-foreground border-border"
                          }`}
                          style={{ boxShadow: isUser ? "0 0 0 2px rgba(13,110,253,0.05)" : undefined }}
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
                          <div className="h-9 w-9 rounded-full bg-muted flex items-center justify-center border border-border">
                            <User className="h-5 w-5 text-muted-foreground" />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {loading && (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> thinking…
                </div>
              )}
            </div>

            {/* Sticky composer (always visible, no page scrolling required) */}
            <div className="sticky bottom-0 bg-background border-t">
              <div className="p-3 flex gap-2">
                <Input
                  placeholder="Write a message…"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                <Button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  className="bg-gradient-primary"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Chat;
