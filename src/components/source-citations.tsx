"use client";

import { useState } from "react";
import * as Popover from "@radix-ui/react-popover";
import type { SourceNode } from "@/hooks/use-chat";
import { useLanguage } from "@/contexts/language-context";

const labels = {
  vi: { sources: "Nguồn tham khảo", page: "Trang" },
  en: { sources: "Sources", page: "Page" },
};

function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
      <path d="M14 2v4a2 2 0 0 0 2 2h4" />
    </svg>
  );
}

function ChevronIcon({ expanded, className }: { expanded: boolean; className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={{ transform: expanded ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s" }}
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

interface SourceCitationsProps {
  sources: SourceNode[];
}

export function SourceCitations({ sources }: SourceCitationsProps) {
  const { language } = useLanguage();
  const t = labels[language];
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex cursor-pointer items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground dark:text-gray-400 dark:hover:text-gray-200"
      >
        <DocumentIcon />
        <span>{t.sources} ({sources.length})</span>
        <ChevronIcon expanded={expanded} />
      </button>

      {expanded && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {sources.map((source) => (
            <Popover.Root key={source.id}>
              <Popover.Trigger asChild>
                <button
                  type="button"
                  className="inline-flex cursor-pointer items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground dark:border-[#414141] dark:text-gray-400 dark:hover:bg-[#414141] dark:hover:text-white"
                >
                  <span className="font-medium text-foreground dark:text-white">[{source.id}]</span>
                  <span className="max-w-[150px] truncate">{source.filename}</span>
                  {source.page != null && (
                    <span className="text-muted-foreground dark:text-gray-500">
                      {t.page} {source.page}
                    </span>
                  )}
                </button>
              </Popover.Trigger>
              <Popover.Portal>
                <Popover.Content
                  className="z-50 max-w-sm rounded-lg border border-gray-200 bg-white p-3 shadow-lg dark:border-[#414141] dark:bg-[#303030]"
                  sideOffset={5}
                  align="start"
                >
                  <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-foreground dark:text-white">
                    <DocumentIcon />
                    <span className="truncate">{source.filename}</span>
                    {source.page != null && (
                      <span className="text-muted-foreground dark:text-gray-400">
                        — {t.page} {source.page}
                      </span>
                    )}
                  </div>
                  <p className="text-xs leading-relaxed text-muted-foreground dark:text-gray-300">
                    {source.text}
                  </p>
                  {source.score != null && (
                    <div className="mt-2 text-[10px] text-muted-foreground dark:text-gray-500">
                      Score: {source.score.toFixed(3)}
                    </div>
                  )}
                  <Popover.Arrow className="fill-white dark:fill-[#303030]" />
                </Popover.Content>
              </Popover.Portal>
            </Popover.Root>
          ))}
        </div>
      )}
    </div>
  );
}
