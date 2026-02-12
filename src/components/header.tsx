"use client";

import { cn } from "@/lib/utils";
import { useScroll } from "@/hooks/use-scroll";
import { useTheme } from "@/contexts/theme-context";
import { useLanguage } from "@/contexts/language-context";
import * as Popover from "@radix-ui/react-popover";
import { useState } from "react";

const SunIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="12" cy="12" r="5" />
    <line x1="12" y1="1" x2="12" y2="3" />
    <line x1="12" y1="21" x2="12" y2="23" />
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
    <line x1="1" y1="12" x2="3" y2="12" />
    <line x1="21" y1="12" x2="23" y2="12" />
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
  </svg>
);

const MoonIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
);

const EllipsisIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
    <circle cx="5" cy="12" r="2" />
    <circle cx="12" cy="12" r="2" />
    <circle cx="19" cy="12" r="2" />
  </svg>
);

const GlobeIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="12" cy="12" r="10" />
    <path d="M2 12h20" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </svg>
);

const TrashIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
  </svg>
);

const labels = {
  vi: {
    lightMode: "Chế độ sáng",
    darkMode: "Chế độ tối",
    language: "Ngôn ngữ",
    clearChat: "Xoá chat",
  },
  en: {
    lightMode: "Light mode",
    darkMode: "Dark mode",
    language: "Language",
    clearChat: "Clear chat",
  },
};

interface HeaderProps {
  onClearChat?: () => void;
}

export function Header({ onClearChat }: HeaderProps) {
  const scrolled = useScroll(10);
  const { theme, toggleTheme } = useTheme();
  const { language, toggleLanguage } = useLanguage();
  const [open, setOpen] = useState(false);

  const t = labels[language];

  return (
    <header
      className={cn(
        "sticky top-0 z-50 w-full border-b border-transparent transition-colors duration-200",
        scrolled &&
          "bg-background/95 supports-[backdrop-filter]:bg-background/50 border-border backdrop-blur-lg"
      )}
    >
      <nav className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between px-4">
        <div className="rounded-md p-2">
          <span className="text-lg font-bold tracking-widest text-foreground">
            WINDBOT
          </span>
        </div>

        <Popover.Root open={open} onOpenChange={setOpen}>
          <Popover.Trigger asChild>
            <button
              type="button"
              className="flex h-9 w-9 items-center justify-center rounded-full text-foreground transition-colors hover:bg-accent"
              aria-label="More options"
            >
              <EllipsisIcon className="h-5 w-5" />
            </button>
          </Popover.Trigger>

          <Popover.Portal>
            <Popover.Content
              align="end"
              sideOffset={8}
              className="z-50 w-52 rounded-xl border border-border bg-popover p-1.5 text-popover-foreground shadow-lg animate-in fade-in-0 zoom-in-95 data-[side=bottom]:slide-in-from-top-2"
            >
              {/* Theme toggle */}
              <button
                type="button"
                onClick={() => {
                  toggleTheme();
                  setOpen(false);
                }}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors hover:bg-accent"
              >
                {theme === "dark" ? (
                  <SunIcon className="h-4 w-4 shrink-0" />
                ) : (
                  <MoonIcon className="h-4 w-4 shrink-0" />
                )}
                <span>{theme === "dark" ? t.lightMode : t.darkMode}</span>
              </button>

              {/* Language selector */}
              <button
                type="button"
                onClick={() => {
                  toggleLanguage();
                  setOpen(false);
                }}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors hover:bg-accent"
              >
                <GlobeIcon className="h-4 w-4 shrink-0" />
                <span>{t.language}</span>
                <span className="ml-auto text-xs text-muted-foreground">
                  {language === "vi" ? "VI" : "EN"}
                </span>
              </button>

              {/* Separator */}
              <div className="my-1 h-px bg-border" />

              {/* Clear chat */}
              <button
                type="button"
                onClick={() => {
                  onClearChat?.();
                  setOpen(false);
                }}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-destructive transition-colors hover:bg-destructive/10"
              >
                <TrashIcon className="h-4 w-4 shrink-0" />
                <span>{t.clearChat}</span>
              </button>
            </Popover.Content>
          </Popover.Portal>
        </Popover.Root>
      </nav>
    </header>
  );
}
