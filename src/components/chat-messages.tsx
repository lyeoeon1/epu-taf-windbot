"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import type { Message } from "@/hooks/use-chat";
import { useLanguage } from "@/contexts/language-context";
import { MermaidBlock } from "./mermaid-block";
import { MermaidErrorBoundary } from "./mermaid-error-boundary";
import { FeedbackPanel } from "./feedback-panel";
import { SourceCitations } from "./source-citations";
import "katex/dist/katex.min.css";

const labels = {
  vi: { copy: "Sao chép", copied: "Đã sao chép!" },
  en: { copy: "Copy", copied: "Copied!" },
};

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function MessageLoading() {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
      className="text-foreground"
    >
      <circle cx="4" cy="12" r="2" fill="currentColor">
        <animate
          id="spinner_qFRN"
          begin="0;spinner_OcgL.end+0.25s"
          attributeName="cy"
          calcMode="spline"
          dur="0.6s"
          values="12;6;12"
          keySplines=".33,.66,.66,1;.33,0,.66,.33"
        />
      </circle>
      <circle cx="12" cy="12" r="2" fill="currentColor">
        <animate
          begin="spinner_qFRN.begin+0.1s"
          attributeName="cy"
          calcMode="spline"
          dur="0.6s"
          values="12;6;12"
          keySplines=".33,.66,.66,1;.33,0,.66,.33"
        />
      </circle>
      <circle cx="20" cy="12" r="2" fill="currentColor">
        <animate
          id="spinner_OcgL"
          begin="spinner_qFRN.begin+0.2s"
          attributeName="cy"
          calcMode="spline"
          dur="0.6s"
          values="12;6;12"
          keySplines=".33,.66,.66,1;.33,0,.66,.33"
        />
      </circle>
    </svg>
  );
}

function CopyIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
      <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

function CopyButton({ text, copyLabel, copiedLabel }: { text: string; copyLabel: string; copiedLabel: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
      const textarea = document.createElement("textarea");
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [text]);

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="flex h-7 w-7 cursor-pointer items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground dark:text-gray-400 dark:hover:bg-[#515151] dark:hover:text-white"
      title={copied ? copiedLabel : copyLabel}
    >
      {copied ? <CheckIcon /> : <CopyIcon />}
    </button>
  );
}

/**
 * Heuristic detection for Mermaid diagram syntax.
 * Checks if the first non-empty line matches a known Mermaid diagram declaration.
 */
function isMermaidCode(code: string): boolean {
  const firstLine = code.trimStart().split("\n")[0].trim();
  return /^(graph\s+(TB|BT|TD|LR|RL)|flowchart\s+(TB|BT|TD|LR|RL)|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitgraph|mindmap|timeline|quadrantChart|sankey|xychart|block-beta)/i.test(firstLine);
}

const markdownComponents: Components = {
  code({ className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || "");
    const lang = match?.[1];
    const codeText = String(children).replace(/\n$/, "");

    // Mermaid blocks: render as visual diagram
    // Primary: explicit ```mermaid tag; Fallback: heuristic detection for block code
    if (lang === "mermaid" || (!lang && codeText.includes("\n") && isMermaidCode(codeText))) {
      return (
        <MermaidErrorBoundary code={codeText}>
          <MermaidBlock code={codeText} />
        </MermaidErrorBoundary>
      );
    }

    // Inline code (no language class, not inside <pre>)
    if (!className) {
      return <code className={className} {...props}>{children}</code>;
    }

    // Block code: render normally
    return <code className={className} {...props}>{children}</code>;
  },
};

function ThumbsUpIcon({ filled, className }: { filled?: boolean; className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M7 10v12" />
      <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z" />
    </svg>
  );
}

function ThumbsDownIcon({ filled, className }: { filled?: boolean; className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M17 14V2" />
      <path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z" />
    </svg>
  );
}

function AssistantMessageActions({
  msg,
  copyLabel,
  copiedLabel,
  sessionId,
}: {
  msg: Message;
  copyLabel: string;
  copiedLabel: string;
  sessionId: string | null;
}) {
  const [vote, setVote] = useState<"up" | "down" | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);

  const handleThumbsUp = useCallback(() => {
    setVote("up");
    setShowFeedback(false);
  }, []);

  const handleThumbsDown = useCallback(() => {
    setVote("down");
    setShowFeedback(true);
  }, []);

  return (
    <>
      <div className="mt-1 flex items-center gap-1">
        <CopyButton text={msg.content} copyLabel={copyLabel} copiedLabel={copiedLabel} />
        <button
          type="button"
          onClick={handleThumbsUp}
          className={`flex h-7 w-7 cursor-pointer items-center justify-center rounded-md transition-colors ${
            vote === "up"
              ? "text-green-500 dark:text-green-400"
              : "text-muted-foreground hover:bg-accent hover:text-foreground dark:text-gray-400 dark:hover:bg-[#515151] dark:hover:text-white"
          }`}
          title="Good response"
        >
          <ThumbsUpIcon filled={vote === "up"} />
        </button>
        <button
          type="button"
          onClick={handleThumbsDown}
          className={`flex h-7 w-7 cursor-pointer items-center justify-center rounded-md transition-colors ${
            vote === "down"
              ? "text-red-500 dark:text-red-400"
              : "text-muted-foreground hover:bg-accent hover:text-foreground dark:text-gray-400 dark:hover:bg-[#515151] dark:hover:text-white"
          }`}
          title="Bad response"
        >
          <ThumbsDownIcon filled={vote === "down"} />
        </button>
        <span className="text-xs text-muted-foreground">
          {formatTime(msg.timestamp)}
        </span>
      </div>
      {msg.sources && msg.sources.length > 0 && (
        <SourceCitations sources={msg.sources} />
      )}
      {showFeedback && vote === "down" && (
        <FeedbackPanel
          sessionId={sessionId}
          messageContent={msg.content}
          onClose={() => setShowFeedback(false)}
        />
      )}
    </>
  );
}

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
  sessionId?: string | null;
  onSendMessage?: (content: string) => void;
}

export function ChatMessages({ messages, isLoading, sessionId, onSendMessage }: ChatMessagesProps) {
  const { language } = useLanguage();
  const t = labels[language];
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const lastAssistantIndex = messages.findLastIndex(
    (m) => m.role === "assistant"
  );

  return (
    <div className="flex flex-col gap-6">
      {messages.map((msg, index) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
        >
          {msg.role === "user" ? (
            <div className="group/msg flex flex-col items-end gap-1 max-w-[80%]">
              <div className="rounded-2xl bg-gray-200 px-4 py-3 text-foreground dark:bg-[#303030] dark:text-white">
                <p className="whitespace-pre-wrap break-words text-left">{msg.content}</p>
              </div>
              <div className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground">
                  {formatTime(msg.timestamp)}
                </span>
                <CopyButton text={msg.content} copyLabel={t.copy} copiedLabel={t.copied} />
              </div>
            </div>
          ) : (
            <div className="group/msg max-w-[80%]">
              {msg.content ? (
                <>
                  <div className="prose max-w-none text-foreground leading-relaxed dark:prose-invert dark:text-white">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm, remarkMath]}
                      rehypePlugins={[rehypeKatex]}
                      components={markdownComponents}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                  <AssistantMessageActions
                    msg={msg}
                    copyLabel={t.copy}
                    copiedLabel={t.copied}
                    sessionId={sessionId ?? null}
                  />
                </>
              ) : (
                isLoading && (
                  <MessageLoading />
                )
              )}
              {msg.suggestions &&
                msg.suggestions.length > 0 &&
                index === lastAssistantIndex &&
                !isLoading && (
                  <div className="mt-4 flex flex-col gap-2">
                    {msg.suggestions.map((suggestion, i) => (
                      <button
                        key={i}
                        onClick={() => onSendMessage?.(suggestion)}
                        className="w-fit cursor-pointer rounded-full border border-gray-300 px-4 py-2.5 text-left text-sm text-foreground transition-colors hover:bg-accent dark:border-[#515151] dark:text-white dark:hover:bg-[#515151]"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
            </div>
          )}
        </div>
      ))}
      <div ref={scrollRef} />
    </div>
  );
}
