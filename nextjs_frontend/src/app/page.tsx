"use client";

import React, { useState, useEffect, useRef } from "react";
import { fetchAPI, getToken, clearToken } from "@/lib/api";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import ChatBubble from "@/components/ChatBubble";
import PdfUploader from "@/components/PdfUploader";
import { ThemeToggle } from "@/components/theme-toggle";
import type { ThinkingStep } from "@/components/AgentThinkingIndicator";

export default function ChatPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ username: string } | null>(null);
  const [sessions, setSessions] = useState<{ session_id: string; created_at: number }[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<{ role: "user" | "agent"; text: string; ts?: string; animateTyping?: boolean }[]>([]);
  const [documents, setDocuments] = useState<{ id: string; filename: string; uploaded_at: string }[]>([]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [streaming, setStreaming] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);

  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Initial Auth Check
  useEffect(() => {
    const init = async () => {
      if (!getToken()) {
        router.push("/login");
        return;
      }
      try {
        const u = await fetchAPI("/auth/me");
        setUser(u);
        await Promise.all([loadSessions(), loadDocuments()]);
      } catch (err) {
        clearToken();
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [router]);

  // Fetch session history when active session changes
  useEffect(() => {
    if (activeSessionId) {
      loadHistory(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  // Auto-scroll to bottom of chat container directly to prevent window scrolling
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, streaming]);

  const loadDocuments = async () => {
    try {
      const data = await fetchAPI("/documents");
      setDocuments(data.documents || []);
    } catch (e) {
      console.error("Failed to load documents", e);
    }
  };

  const loadSessions = async () => {
    const data = await fetchAPI("/sessions");
    setSessions(data.sessions);
    if (!activeSessionId && data.sessions.length > 0) {
      setActiveSessionId(data.sessions[0].session_id);
    }
  };

  const loadHistory = async (sid: string) => {
    const data = await fetchAPI(`/sessions/${sid}/history`);
    const msgs = (data.messages || []).map((msg: { role: string; text: string; ts?: string; animateTyping?: boolean }) => ({
      ...msg,
      text: msg.role === "agent" ? msg.text.replace(/\s*\[DONE\]\s*/g, "").trim() : msg.text,
      animateTyping: false, // Old messages don't animate
    }));
    setMessages(msgs);
  };

  const handleNewSession = async () => {
    try {
      const data = await fetchAPI("/sessions/new", { method: "POST" });
      setActiveSessionId(data.session_id);
      setMessages([]);
      await loadSessions();
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogout = () => {
    clearToken();
    router.push("/login");
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    let targetSessionId = activeSessionId;
    if (!targetSessionId) {
      const newsess = await fetchAPI("/sessions/new", { method: "POST" });
      targetSessionId = newsess.session_id;
      setActiveSessionId(targetSessionId);
    }

    const formData = new FormData();
    formData.append("file", file);
    if (targetSessionId) {
      formData.append("session_id", targetSessionId);
    }

    const token = getToken();
    setMessages((prev) => [...prev, { role: "user", text: `[Uploaded PDF: ${file.name}]` }]);
    setStreaming(true);

    // Add empty agent message to be populated via SSE stream (shows buffering animation initially)
    setMessages((prev) => [...prev, { role: "agent", text: "", animateTyping: true }]);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001/api"}/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!response.body) throw new Error("No body in response");

      await processStream(response.body);
    } catch (e) {
      console.error(e);
    } finally {
      setIsUploading(false);
      setStreaming(false);
      setThinkingSteps([]);
      await Promise.all([loadSessions(), loadDocuments()]);
    }
  };

  const processStream = async (body: ReadableStream<Uint8Array>) => {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let done = false;
    let stepCounter = 0;
    let currentEventType = "message";

    // Read the EventSource stream format manually since fetch doesn't native parse SSE
    while (!done) {
      const { value, done: doneReading } = await reader.read();
      done = doneReading;
      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");
        for (const line of lines) {
          // Track event type across lines (SSE multi-line format)
          if (line.startsWith("event: ")) {
            currentEventType = line.substring(7).trim();
            continue;
          }

          if (!line.startsWith("data: ")) continue;

          const dataStr = line.substring(6);

          // Reset event type after consuming the data line
          const eventType = currentEventType;
          currentEventType = "message";

          if (dataStr === "[DONE]") {
            done = true;
            break;
          }

          if (!dataStr) continue;

          // ── Error event from backend ──
          if (eventType === "error") {
            setMessages((prev) => {
              const newArr = [...prev];
              const lastIdx = newArr.length - 1;
              if (lastIdx >= 0 && newArr[lastIdx].role === "agent") {
                newArr[lastIdx] = { ...newArr[lastIdx], text: "Sorry, something went wrong. Please try again.", animateTyping: false };
              }
              return newArr;
            });
            done = true;
            break;
          }

          // Try to parse as JSON (new format)
          let parsed: { type?: string; event?: string; tool?: string; agent?: string; content?: string } | null = null;
          try {
            parsed = JSON.parse(dataStr);
          } catch {
            // Not JSON — treat as raw text (backward compat)
            parsed = null;
          }

          if (parsed && parsed.type === "status") {
            // ── Status event: tool call or agent transfer ──
            const stepName = parsed.event === "agent_transfer" ? (parsed.agent || "Agent") : (parsed.tool || "Processing");
            const newStep: ThinkingStep = {
              id: `step-${++stepCounter}`,
              type: parsed.event === "agent_transfer" ? "agent_transfer" : "tool_call",
              name: stepName,
              agent: parsed.agent || "",
              status: "active",
              timestamp: Date.now(),
            };

            setThinkingSteps((prev) => {
              // Mark all previous active steps as done
              const updated = prev.map((s) =>
                s.status === "active" ? { ...s, status: "done" as const } : s
              );
              return [...updated, newStep];
            });
          } else if (parsed && parsed.type === "text" && parsed.content) {
            // ── Text event: final response content ──
            // Mark all thinking steps as done when text arrives
            setThinkingSteps((prev) =>
              prev.map((s) => (s.status === "active" ? { ...s, status: "done" as const } : s))
            );
            setMessages((prev) => {
              const newArr = [...prev];
              const lastIdx = newArr.length - 1;
              // Safety check: if there's no agent message yet (race condition), create one
              if (lastIdx < 0 || newArr[lastIdx].role !== "agent") {
                newArr.push({ role: "agent", text: parsed!.content || "", animateTyping: true });
              } else {
                newArr[lastIdx] = { ...newArr[lastIdx], text: newArr[lastIdx].text + parsed!.content };
              }
              return newArr;
            });
          } else {
            // ── Fallback: raw text (backward compat) ──
            const rawText = parsed?.content || dataStr;
            setMessages((prev) => {
              const newArr = [...prev];
              const lastIdx = newArr.length - 1;
              // Safety check: if there's no agent message yet (race condition), create one
              if (lastIdx < 0 || newArr[lastIdx].role !== "agent") {
                newArr.push({ role: "agent", text: rawText, animateTyping: true });
              } else {
                newArr[lastIdx] = { ...newArr[lastIdx], text: newArr[lastIdx].text + rawText };
              }
              return newArr;
            });
          }
        }
      }
    }

    // Clean up: strip any [DONE] marker that the LLM may have included in its response text
    setMessages((prev) => {
      const newArr = [...prev];
      const lastIdx = newArr.length - 1;
      if (lastIdx >= 0 && newArr[lastIdx].role === "agent") {
        const cleaned = newArr[lastIdx].text.replace(/\s*\[DONE\]\s*/g, "").trim();
        newArr[lastIdx] = { ...newArr[lastIdx], text: cleaned };
      }
      return newArr;
    });
  };

  const sendMessage = async (msgText: string) => {
    if (!msgText.trim() || streaming) return;

    let targetSessionId = activeSessionId;
    if (!targetSessionId) {
      const newsess = await fetchAPI("/sessions/new", { method: "POST" });
      targetSessionId = newsess.session_id;
      setActiveSessionId(targetSessionId);
    }

    const token = getToken();
    setMessages((prev) => [...prev, { role: "user", text: msgText }]);
    setStreaming(true);
    setMessages((prev) => [...prev, { role: "agent", text: "", animateTyping: true }]);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001/api"}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ message: msgText, session_id: targetSessionId }),
      });

      if (!response.body) throw new Error("No body in response");

      await processStream(response.body);
    } catch (e) {
      console.error(e);
    } finally {
      setStreaming(false);
      setThinkingSteps([]);
      await loadSessions(); // Refresh history
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || streaming) return;
    const msgText = input.trim();
    setInput("");
    await sendMessage(msgText);
  };

  if (loading) return null;

  return (
    <div className="flex fixed inset-0 overflow-hidden">
      {/* Absolute Positioned Glowing Rings for depth matching video */}
      <div className="bg-glow-effect"></div>

      {/* Main Layout Layer */}
      <div className="flex z-10 w-full h-full relative backdrop-blur-[2px]">
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={setActiveSessionId}
          onNewSession={handleNewSession}
          onLogout={handleLogout}
          user={user}
          onQuickAction={sendMessage}
          onUpload={handleUpload}
          isUploading={isUploading}
          documents={documents}
        />

        <main className="flex-1 flex flex-col relative z-20 h-full overflow-hidden">
          {/* Top Fade-out Mask */}
          <div className="absolute top-0 left-0 right-0 h-10 bg-gradient-to-b from-[var(--bg-color)] to-transparent z-10 pointer-events-none"></div>

          {/* Theme Toggle Button */}
          <div className="absolute top-4 right-4 z-50">
            <ThemeToggle />
          </div>

          {/* Chat Area */}
          <div
            ref={chatContainerRef}
            className="flex-1 overflow-y-auto p-4 md:p-8 space-y-2 custom-scrollbar"
          >
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center max-w-2xl mx-auto space-y-12 animate-fade-in relative">

                {/* Neon Icon */}
                <div className="relative group perspective-1000">
                  <div className="absolute inset-0 bg-gradient-to-tr from-[#1e3a5f] via-[#2c5282] to-[#c9a84c] rounded-3xl blur-xl opacity-50 group-hover:opacity-100 group-hover:blur-2xl transition-all duration-700"></div>
                  <div className="relative w-28 h-28 bg-[var(--chat-agent-bg)] backdrop-blur-xl border border-[var(--glass-border)] rounded-3xl flex items-center justify-center transform group-hover:-translate-y-2 group-hover:rotate-6 transition-all duration-500 shadow-[var(--glass-shadow)]">
                    <svg className="w-14 h-14 text-[var(--color-primary-500)] drop-shadow-[0_0_15px_rgba(255,255,255,0.8)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                  </div>
                </div>

                <div className="text-center space-y-5">
                  <h2 className="text-5xl md:text-6xl font-black bg-gradient-to-r from-[#1e3a5f] via-[#2c5282] to-[#1e3a5f] dark:from-[#c9a84c] dark:via-[#d4af37] dark:to-[#e8c547] bg-clip-text text-transparent pb-2 tracking-tight drop-shadow-[0_0_20px_rgba(30,58,95,0.1)] dark:drop-shadow-[0_0_20px_rgba(201,168,76,0.2)]" style={{ fontFamily: 'var(--font-serif)' }}>
                    Good evening, {user?.username || "Guest"}.
                  </h2>
                  <p className="text-lg md:text-xl text-[#1e3a5f]/60 dark:text-[#c8c3b8]/70 font-light tracking-wide">
                    How can I assist your learning journey today?
                  </p>
                </div>

                <div className="w-full max-w-xl scale-110 mt-8 hover:scale-[1.12] transition-transform duration-500">
                  <PdfUploader onUpload={handleUpload} isUploading={isUploading} />
                </div>
              </div>
            ) : (
              <div className="max-w-4xl mx-auto w-full pb-4 pt-10">
                {messages.map((msg, idx) => (
                  <ChatBubble
                    key={idx}
                    role={msg.role}
                    text={msg.text}
                    ts={msg.ts}
                    isStreaming={streaming && idx === messages.length - 1 && msg.role === "agent"}
                    animateTyping={msg.animateTyping}
                    thinkingSteps={streaming && idx === messages.length - 1 && msg.role === "agent" ? thinkingSteps : undefined}
                    onOptionClick={msg.role === "agent" && idx === messages.length - 1 && !streaming ? (opt) => sendMessage(opt) : undefined}
                    onPublish={msg.role === "agent" && idx === messages.length - 1 && !streaming ? () => sendMessage("Please publish this recently generated item to the community.") : undefined}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Input Area (Floating Dark Glass Pill) */}
          <div className="shrink-0 p-4 md:p-6 bg-[var(--bg-color)]/80 backdrop-blur-xl border-t border-[var(--glass-border)] z-30">
            <div className="max-w-4xl mx-auto relative">

              {/* Subtle background glow for input focus */}
              <div className={`absolute inset-0 bg-[#1e3a5f]/15 rounded-full blur-2xl transition-opacity duration-500 pointer-events-none ${input.trim() ? "opacity-100" : "opacity-0"}`}></div>

              <form onSubmit={handleSend} className="relative group">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend(e);
                    }
                  }}
                  disabled={streaming || isUploading}
                  placeholder="Chat with LMS Agent..."
                  className="w-full bg-[var(--chat-agent-bg)] text-[var(--text-color)] backdrop-blur-2xl border border-[var(--glass-border)] rounded-full pl-8 pr-16 py-[18px] focus:outline-none focus:border-[#c9a84c]/30 focus:ring-4 focus:ring-[#c9a84c]/15 resize-none overflow-hidden min-h-[60px] max-h-[150px] text-base placeholder-[#1e3a5f]/30 dark:placeholder-[#c8c3b8]/40 shadow-[var(--glass-shadow)] transition-all duration-300 disabled:opacity-50"
                  rows={1}
                />

                <button
                  type="submit"
                  disabled={!input.trim() || streaming || isUploading}
                  className="absolute right-2 top-2 p-3 bg-gradient-to-r from-[#1e3a5f] to-[#2c5282] text-white rounded-full hover:shadow-[0_0_20px_rgba(30,58,95,0.5)] disabled:bg-slate-800 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-500 transition-all duration-300 active:scale-95"
                  title="Send message"
                >
                  <svg className="w-5 h-5 translate-x-px translate-y-px transform rotate-45" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </form>

              <div className="text-center mt-4">
                <span className="text-[12px] font-medium text-[#1e3a5f]/40 dark:text-[#c8c3b8]/40 tracking-widest uppercase">
                  AI responses can be inaccurate. Please verify.
                </span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
