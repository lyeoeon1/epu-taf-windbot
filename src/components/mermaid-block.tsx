"use client";

import { useEffect, useRef, useState, useCallback } from "react";
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

function ExpandIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 3H5a2 2 0 0 0-2 2v3" />
      <path d="M21 8V5a2 2 0 0 0-2-2h-3" />
      <path d="M3 16v3a2 2 0 0 0 2 2h3" />
      <path d="M16 21h3a2 2 0 0 0 2-2v-3" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
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

/**
 * Post-process rendered SVG to fix truncated node labels.
 * Mermaid calculates node width too small for long text.
 * This reads actual text width and resizes the node rect/polygon to fit.
 */
function fixNodeWidths(container: HTMLDivElement) {
  const svg = container.querySelector("svg");
  if (!svg) return;

  const nodes = svg.querySelectorAll(".node");
  nodes.forEach((node) => {
    // Get all text elements in this node
    const texts = node.querySelectorAll("text");
    if (texts.length === 0) return;

    // Calculate max text width across all lines
    let maxTextWidth = 0;
    texts.forEach((text) => {
      const bbox = text.getBBox();
      if (bbox.width > maxTextWidth) maxTextWidth = bbox.width;
    });

    if (maxTextWidth === 0) return;

    const padding = 16; // padding on each side
    const neededWidth = maxTextWidth + padding * 2;

    // Find the shape element (rect, polygon, or path)
    const rect = node.querySelector("rect");
    if (rect) {
      const currentWidth = parseFloat(rect.getAttribute("width") || "0");
      if (neededWidth > currentWidth) {
        const diff = neededWidth - currentWidth;
        rect.setAttribute("width", String(neededWidth));
        // Shift rect left by half the diff to keep centered
        const currentX = parseFloat(rect.getAttribute("x") || "0");
        rect.setAttribute("x", String(currentX - diff / 2));
      }
    }

    // Also handle foreignObject if present (htmlLabels: true fallback)
    const fo = node.querySelector("foreignObject");
    if (fo) {
      const currentWidth = parseFloat(fo.getAttribute("width") || "0");
      if (neededWidth > currentWidth) {
        const diff = neededWidth - currentWidth;
        fo.setAttribute("width", String(neededWidth));
        const currentX = parseFloat(fo.getAttribute("x") || "0");
        fo.setAttribute("x", String(currentX - diff / 2));
      }
    }
  });

  // Update SVG viewBox to fit expanded nodes
  const svgBBox = svg.getBBox();
  if (svgBBox.width > 0 && svgBBox.height > 0) {
    const pad = 10;
    svg.setAttribute("viewBox", `${svgBBox.x - pad} ${svgBBox.y - pad} ${svgBBox.width + pad * 2} ${svgBBox.height + pad * 2}`);
    svg.setAttribute("width", String(svgBBox.width + pad * 2));
    svg.setAttribute("height", String(svgBBox.height + pad * 2));
  }
}

let mermaidRenderCounter = 0;

export function MermaidBlock({ code }: MermaidBlockProps) {
  const { theme } = useTheme();
  const svgRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const { containerRef, contentRef, state, isPanning, zoomIn, zoomOut, fitToContainer, handlers } = usePanZoom();
  const fitRef = useRef(fitToContainer);
  fitRef.current = fitToContainer;

  // Close expanded popup on Escape key
  useEffect(() => {
    if (!isExpanded) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsExpanded(false);
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isExpanded]);

  const toggleExpand = useCallback(() => {
    setIsExpanded((prev) => !prev);
    // Re-fit after expanding/collapsing
    requestAnimationFrame(() => fitRef.current());
  }, []);

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
        flowchart: {
          useMaxWidth: false,
          htmlLabels: true,
          nodeSpacing: 30,
          rankSpacing: 40,
        },
      });

      try {
        const sanitized = sanitizeMermaidCode(stableCode!);
        const renderId = `mermaid-${++mermaidRenderCounter}`;
        const { svg } = await mermaid.render(renderId, sanitized);
        if (!cancelled && svgRef.current) {
          svgRef.current.innerHTML = svg;

          // Post-process: fix truncated text by expanding nodes to fit content
          fixNodeWidths(svgRef.current);
          setError(null);

          // Auto-fit after render (use ref to avoid dep cycle)
          requestAnimationFrame(() => {
            if (!cancelled) {
              fitRef.current();
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
  }, [stableCode, theme, isExpanded]);

  if (error) {
    return (
      <pre className="mermaid-error">
        <code>{code}</code>
      </pre>
    );
  }

  const scalePercent = Math.round(state.scale * 100);

  const diagramContent = (
    <>
      <div className={isExpanded ? "mermaid-toolbar mermaid-toolbar-visible" : "mermaid-toolbar"}>
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
        <button type="button" onClick={toggleExpand} aria-label={isExpanded ? "Close" : "Expand"}>
          {isExpanded ? <CloseIcon /> : <ExpandIcon />}
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
    </>
  );

  if (isExpanded) {
    return (
      <>
        <div className="mermaid-wrapper">
          <div className="mermaid-viewport" style={{ height: 80, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--muted-foreground)", fontSize: "0.875em", cursor: "pointer" }} onClick={toggleExpand}>
            Click to view diagram
          </div>
        </div>
        <div className="mermaid-overlay" onClick={toggleExpand}>
          <div className="mermaid-popup" onClick={(e) => e.stopPropagation()}>
            <div className="mermaid-wrapper" style={{ margin: 0, height: "100%" }}>
              {diagramContent}
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <div className="mermaid-wrapper">
      {diagramContent}
    </div>
  );
}
