"use client";

import * as Popover from "@radix-ui/react-popover";
import type { SourceNode } from "@/hooks/use-chat";
import { useLanguage } from "@/contexts/language-context";

const labels = {
  vi: { page: "Trang" },
  en: { page: "Page" },
};

function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="12"
      height="12"
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

interface SourceCitationsProps {
  sources: SourceNode[];
}

export function SourceCitations({ sources }: SourceCitationsProps) {
  const { language } = useLanguage();
  const t = labels[language];

  if (!sources || sources.length === 0) return null;

  return (
    <span className="inline">
      {sources.map((source) => (
        <Popover.Root key={source.id}>
          <Popover.Trigger asChild>
            <button
              type="button"
              className="ml-0.5 inline-flex cursor-pointer items-center justify-center rounded bg-gray-200 px-1 py-0.5 align-super text-[10px] font-medium text-muted-foreground transition-colors hover:bg-gray-300 dark:bg-[#414141] dark:text-gray-400 dark:hover:bg-[#515151]"
            >
              {source.id}
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
              <Popover.Arrow className="fill-white dark:fill-[#303030]" />
            </Popover.Content>
          </Popover.Portal>
        </Popover.Root>
      ))}
    </span>
  );
}
