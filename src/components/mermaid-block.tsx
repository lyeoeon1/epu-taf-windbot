"use client";

import { useEffect, useRef, useState, useId } from "react";
import { useTheme } from "@/contexts/theme-context";

interface MermaidBlockProps {
  code: string;
}

export function MermaidBlock({ code }: MermaidBlockProps) {
  const { theme } = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const uniqueId = useId().replace(/:/g, "-");

  useEffect(() => {
    let cancelled = false;

    async function renderDiagram() {
      const { default: mermaid } = await import("mermaid");

      mermaid.initialize({
        startOnLoad: false,
        theme: theme === "dark" ? "dark" : "default",
        themeVariables: {
          background: "transparent",
        },
        fontFamily: "inherit",
      });

      try {
        const { svg } = await mermaid.render(`mermaid-${uniqueId}`, code);
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg;
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to render diagram");
        }
      }
    }

    renderDiagram();

    return () => {
      cancelled = true;
    };
  }, [code, theme, uniqueId]);

  if (error) {
    return (
      <pre className="mermaid-error">
        <code>{code}</code>
      </pre>
    );
  }

  return (
    <div className="mermaid-container" ref={containerRef}>
      <div className="mermaid-loading">Loading diagram…</div>
    </div>
  );
}
