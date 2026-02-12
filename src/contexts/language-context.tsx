"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

type Language = "vi" | "en";

interface LanguageContextValue {
  language: Language;
  toggleLanguage: () => void;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

function getInitialLanguage(): Language {
  if (typeof window === "undefined") return "vi";

  const stored = localStorage.getItem("language");
  if (stored === "vi" || stored === "en") return stored;

  return "vi";
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>("vi");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const initial = getInitialLanguage();
    setLanguage(initial);
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    localStorage.setItem("language", language);
  }, [language, mounted]);

  const toggleLanguage = useCallback(() => {
    setLanguage((prev) => (prev === "vi" ? "en" : "vi"));
  }, []);

  return (
    <LanguageContext.Provider value={{ language, toggleLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
}
