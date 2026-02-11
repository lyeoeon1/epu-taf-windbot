"use client";

import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import type { Message } from "@/hooks/use-chat";
import "katex/dist/katex.min.css";

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
}

export function ChatMessages({ messages, isLoading }: ChatMessagesProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col gap-6">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
        >
          {msg.role === "user" ? (
            <div className="max-w-[80%] rounded-2xl bg-[#303030] px-4 py-3 text-white">
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          ) : (
            <div className="max-w-[80%]">
              {msg.content ? (
                <div className="prose prose-invert max-w-none text-white leading-relaxed">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>
              ) : (
                isLoading && (
                  <div className="flex items-center gap-1.5 py-2">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-gray-400" />
                    <span className="h-2 w-2 animate-pulse rounded-full bg-gray-400 [animation-delay:150ms]" />
                    <span className="h-2 w-2 animate-pulse rounded-full bg-gray-400 [animation-delay:300ms]" />
                  </div>
                )
              )}
            </div>
          )}
        </div>
      ))}
      <div ref={scrollRef} />
    </div>
  );
}
