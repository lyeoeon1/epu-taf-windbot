"use client";

import { useCallback, useRef, useState } from "react";

export interface SourceNode {
  id: number;
  text: string;
  filename: string;
  page?: number;
  score: number | null;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  suggestions?: string[];
  sources?: SourceNode[];
  timestamp: number;
}

export interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  sessionId: string | null;
  sendMessage: (content: string) => Promise<void>;
  clearChat: () => void;
}

const errorLabels = {
  vi: { genericError: "Xin lỗi, đã xảy ra lỗi. Vui lòng kiểm tra backend đang chạy." },
  en: { genericError: "Sorry, an error occurred. Please check that the backend is running." },
};

export function useChat(language: string = "vi"): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const sessionIdRef = useRef<string | null>(null);

  const ensureSession = useCallback(async (): Promise<string> => {
    if (sessionIdRef.current) return sessionIdRef.current;

    const res = await fetch("/api/chat/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "New Chat", language }),
    });

    if (!res.ok) throw new Error("Failed to create chat session");

    const data = await res.json();
    sessionIdRef.current = data.id;
    setSessionId(data.id);
    return data.id;
  }, [language]);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      setIsLoading(true);

      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: content.trim(),
        timestamp: Date.now(),
      };

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "",
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);

      try {
        const sessionId = await ensureSession();

        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            message: content.trim(),
            language,
          }),
        });

        if (!res.ok) {
          const errorText = await res.text();
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessage.id
                ? { ...m, content: `Error: ${errorText || res.statusText}` }
                : m
            )
          );
          return;
        }

        const reader = res.body?.getReader();
        if (!reader) return;

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;

            try {
              const data = JSON.parse(line.slice(6));
              if (data.suggestions) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMessage.id
                      ? { ...m, suggestions: data.suggestions }
                      : m
                  )
                );
              }
              if (data.sources) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMessage.id
                      ? { ...m, sources: data.sources, ...(data.content ? { content: data.content } : {}) }
                      : m
                  )
                );
              }
              if (data.token) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMessage.id
                      ? { ...m, content: m.content + data.token }
                      : m
                  )
                );
              }
              // Continue reading after "done" to receive suggestions
            } catch {
              // Skip malformed SSE lines
            }
          }
        }

        // Process any remaining data in the buffer
        if (buffer.trim().startsWith("data: ")) {
          try {
            const data = JSON.parse(buffer.trim().slice(6));
            if (data.suggestions) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMessage.id
                    ? { ...m, suggestions: data.suggestions }
                    : m
                )
              );
            }
            if (data.sources) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMessage.id
                    ? { ...m, sources: data.sources, ...(data.content ? { content: data.content } : {}) }
                    : m
                )
              );
            }
          } catch {
            // Skip malformed data
          }
        }
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessage.id
              ? {
                  ...m,
                  content:
                    errorLabels[language as keyof typeof errorLabels]?.genericError || errorLabels.en.genericError,
                }
              : m
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, language, ensureSession]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    sessionIdRef.current = null;
    setSessionId(null);
  }, []);

  return { messages, isLoading, sessionId, sendMessage, clearChat };
}
