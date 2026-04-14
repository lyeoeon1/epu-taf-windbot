"use client";

import { useEffect, useRef, useState, useId } from "react";
import { useTheme } from "@/contexts/theme-context";
import { usePanZoom } from "@/hooks/use-pan-zoom";

interface MermaidBlockProps {
  code: string;
}

const lightThemeVariables = {
  background: "transparent",
  fontFamily: "inherit",
  fontSize: "14px",
  primaryColor: "#e8eaed",
  primaryTextColor: "#171717",
  primaryBorderColor: "#d1d5db",
  secondaryColor: "#f0f4f8",
  secondaryTextColor: "#171717",
  secondaryBorderColor: "#cbd5e1",
  tertiaryColor: "#fef3c7",
  tertiaryTextColor: "#171717",
  tertiaryBorderColor: "#fcd34d",
  lineColor: "#6b7280",
  textColor: "#171717",
  noteBkgColor: "#fef9c3",
  noteTextColor: "#171717",
  noteBorderColor: "#facc15",
  nodeBorder: "#9ca3af",
  clusterBkg: "#f9fafb",
  clusterBorder: "#d1d5db",
  defaultLinkColor: "#6b7280",
  titleColor: "#171717",
  edgeLabelBackground: "#ffffff",
  actorBkg: "#e8eaed",
  actorTextColor: "#171717",
  actorBorder: "#9ca3af",
  actorLineColor: "#9ca3af",
  signalColor: "#171717",
  signalTextColor: "#171717",
  labelBoxBkgColor: "#f5f5f5",
  labelBoxBorderColor: "#d1d5db",
  labelTextColor: "#171717",
  loopTextColor: "#171717",
  activationBorderColor: "#9ca3af",
  activationBkgColor: "#e5e7eb",
  sequenceNumberColor: "#ffffff",
};

const darkThemeVariables = {
  background: "transparent",
  fontFamily: "inherit",
  fontSize: "14px",
  primaryColor: "#2d3748",
  primaryTextColor: "#fafafa",
  primaryBorderColor: "#4a5568",
  secondaryColor: "#1e293b",
  secondaryTextColor: "#fafafa",
  secondaryBorderColor: "#475569",
  tertiaryColor: "#44337a",
  tertiaryTextColor: "#fafafa",
  tertiaryBorderColor: "#6b46c1",
  lineColor: "#a1a1aa",
  textColor: "#fafafa",
  noteBkgColor: "#854d0e",
  noteTextColor: "#fafafa",
  noteBorderColor: "#ca8a04",
  nodeBorder: "#6b7280",
  clusterBkg: "#1f2937",
  clusterBorder: "#4a5568",
  defaultLinkColor: "#a1a1aa",
  titleColor: "#fafafa",
  edgeLabelBackground: "#18181b",
  actorBkg: "#2d3748",
  actorTextColor: "#fafafa",
  actorBorder: "#6b7280",
  actorLineColor: "#6b7280",
  signalColor: "#fafafa",
  signalTextColor: "#fafafa",
  labelBoxBkgColor: "#27272a",
  labelBoxBorderColor: "#4a5568",
  labelTextColor: "#fafafa",
  loopTextColor: "#fafafa",
  activationBorderColor: "#6b7280",
  activationBkgColor: "#374151",
  sequenceNumberColor: "#18181b",
};

function ZoomInIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="11" y1="8" x2="11" y2="14" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}

function ZoomOutIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}

function FitIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 3 21 3 21 9" />
      <polyline points="9 21 3 21 3 15" />
      <line x1="21" y1="3" x2="14" y2="10" />
      <line x1="3" y1="21" x2="10" y2="14" />
    </svg>
  );
}

/**
 * Sanitize Mermaid code to fix common LLM-generated syntax issues.
 * Wraps ALL unquoted node labels in quotes to handle Vietnamese text,
 * parentheses, and other special characters that break the Mermaid parser.
 */
function sanitizeMermaidCode(raw: string): string {
  // Process each line individually
  return raw
    .split("\n")
    .map((line) => {
      // Skip lines that are just graph/flowchart declarations or arrows-only
      if (/^\s*(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitgraph|mindmap|timeline)\b/i.test(line)) {
        return line;
      }

      // Quote all unquoted bracket labels: A[text] → A["text"]
      // But skip already-quoted: A["text"] stays unchanged
      return line.replace(
        /\[(?!")((?:[^\[\]"]+))\]/g,
        (_match, content) => `["${content}"]`
      );
    })
    .join("\n");
}

export function MermaidBlock({ code }: MermaidBlockProps) {
  const { theme } = useTheme();
  const svgRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const uniqueId = useId().replace(/:/g, "-");
  const { containerRef, contentRef, state, isPanning, zoomIn, zoomOut, fitToContainer, handlers } = usePanZoom();

  // Debounce rendering: wait for code to stop changing (streaming complete)
  // before attempting to render. This prevents errors from partial code
  // during SSE streaming.
  const [stableCode, setStableCode] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    setStableCode(null);
    const timer = setTimeout(() => {
      setStableCode(code);
    }, 500); // 500ms debounce — streaming tokens arrive faster than this
    return () => clearTimeout(timer);
  }, [code]);

  useEffect(() => {
    if (!stableCode) return;
    let cancelled = false;

    async function renderDiagram() {
      const { default: mermaid } = await import("mermaid");

      const themeVars = theme === "dark" ? darkThemeVariables : lightThemeVariables;

      mermaid.initialize({
        startOnLoad: false,
        theme: "base",
        themeVariables: themeVars,
      });

      try {
        const sanitized = sanitizeMermaidCode(stableCode!);
        const { svg } = await mermaid.render(`mermaid-${uniqueId}`, sanitized);
        if (!cancelled && svgRef.current) {
          svgRef.current.innerHTML = svg;
          setError(null);

          // Auto-fit after render
          requestAnimationFrame(() => {
            if (!cancelled) {
              fitToContainer();
            }
          });
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
  }, [stableCode, theme, uniqueId, fitToContainer]);

  if (error) {
    return (
      <pre className="mermaid-error">
        <code>{code}</code>
      </pre>
    );
  }

  const scalePercent = Math.round(state.scale * 100);

  return (
    <div className="mermaid-wrapper">
      <div className="mermaid-toolbar">
        <button type="button" onClick={zoomOut} aria-label="Zoom out">
          <ZoomOutIcon />
        </button>
        <span className="zoom-level">{scalePercent}%</span>
        <button type="button" onClick={zoomIn} aria-label="Zoom in">
          <ZoomInIcon />
        </button>
        <button type="button" onClick={fitToContainer} aria-label="Fit to view">
          <FitIcon />
        </button>
      </div>
      <div
        ref={containerRef}
        className={`mermaid-viewport${isPanning ? " is-panning" : ""}`}
        {...handlers}
      >
        <div
          ref={contentRef}
          className="mermaid-content"
          style={{
            transform: `scale(${state.scale}) translate(${state.translateX}px, ${state.translateY}px)`,
          }}
        >
          <div ref={svgRef}>
            <div className="mermaid-loading">Loading diagram…</div>
          </div>
        </div>
      </div>
    </div>
  );
}
