"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const MIN_SCALE = 0.25;
const MAX_SCALE = 4;
const ZOOM_STEP = 0.15;

interface PanZoomState {
  scale: number;
  translateX: number;
  translateY: number;
}

export function usePanZoom() {
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<PanZoomState>({
    scale: 1,
    translateX: 0,
    translateY: 0,
  });
  const [isPanning, setIsPanning] = useState(false);

  const dragStart = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    startTx: number;
    startTy: number;
  } | null>(null);

  // Track active pointers for pinch-to-zoom
  const pointers = useRef<Map<number, { x: number; y: number }>>(new Map());
  const lastPinchDist = useRef<number | null>(null);

  const clampScale = (s: number) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, s));

  const zoomIn = useCallback(() => {
    setState((prev) => {
      const newScale = clampScale(prev.scale + ZOOM_STEP);
      return { ...prev, scale: newScale };
    });
  }, []);

  const zoomOut = useCallback(() => {
    setState((prev) => {
      const newScale = clampScale(prev.scale - ZOOM_STEP);
      return { ...prev, scale: newScale };
    });
  }, []);

  const resetView = useCallback(() => {
    if (!containerRef.current || !contentRef.current) {
      setState({ scale: 1, translateX: 0, translateY: 0 });
      return;
    }
    const svg = contentRef.current.querySelector("svg");
    if (!svg) {
      setState({ scale: 1, translateX: 0, translateY: 0 });
      return;
    }
    const containerWidth = containerRef.current.clientWidth;
    const svgWidth = svg.getBoundingClientRect().width / (state.scale || 1);
    if (svgWidth > containerWidth && containerWidth > 0) {
      setState({
        scale: containerWidth / svgWidth,
        translateX: 0,
        translateY: 0,
      });
    } else {
      setState({ scale: 1, translateX: 0, translateY: 0 });
    }
  }, [state.scale]);

  const fitToContainer = useCallback(() => {
    if (!containerRef.current || !contentRef.current) {
      setState({ scale: 1, translateX: 0, translateY: 0 });
      return;
    }
    const svg = contentRef.current.querySelector("svg");
    if (!svg) {
      setState({ scale: 1, translateX: 0, translateY: 0 });
      return;
    }
    // Get natural SVG dimensions from attributes
    const widthAttr = svg.getAttribute("width");
    const heightAttr = svg.getAttribute("height");
    const naturalWidth = parseFloat(widthAttr || "0");
    const naturalHeight = parseFloat(heightAttr || "0");
    const containerWidth = containerRef.current.clientWidth;
    const containerHeight = containerRef.current.clientHeight;

    if (naturalWidth > 0 && naturalHeight > 0 && containerWidth > 0 && containerHeight > 0) {
      const scaleX = containerWidth / naturalWidth;
      const scaleY = containerHeight / naturalHeight;
      const fitScale = Math.min(scaleX, scaleY, 1); // Don't zoom beyond 1
      setState({ scale: fitScale, translateX: 0, translateY: 0 });
    } else {
      setState({ scale: 1, translateX: 0, translateY: 0 });
    }
  }, []);

  const getDistance = (p1: { x: number; y: number }, p2: { x: number; y: number }) => {
    return Math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2);
  };

  // Use ref to always read latest state in pointer handlers (avoid stale closures)
  const stateRef = useRef(state);
  stateRef.current = state;

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      try {
        pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });

        if (pointers.current.size === 1) {
          dragStart.current = {
            pointerId: e.pointerId,
            startX: e.clientX,
            startY: e.clientY,
            startTx: stateRef.current.translateX,
            startTy: stateRef.current.translateY,
          };
          setIsPanning(true);
          (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
        } else if (pointers.current.size === 2) {
          const pts = Array.from(pointers.current.values());
          lastPinchDist.current = getDistance(pts[0], pts[1]);
          dragStart.current = null;
          setIsPanning(false);
        }
      } catch { /* prevent crash from propagating to error boundary */ }
    },
    []
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      try {
        pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });

        if (pointers.current.size === 2 && lastPinchDist.current !== null) {
          const pts = Array.from(pointers.current.values());
          const newDist = getDistance(pts[0], pts[1]);
          const ratio = newDist / lastPinchDist.current;
          lastPinchDist.current = newDist;

          setState((prev) => {
            const newScale = clampScale(prev.scale * ratio);
            return { ...prev, scale: newScale };
          });
          return;
        }

        const drag = dragStart.current;
        if (!drag || e.pointerId !== drag.pointerId) return;

        const dx = e.clientX - drag.startX;
        const dy = e.clientY - drag.startY;

        setState((prev) => ({
          ...prev,
          translateX: drag.startTx + dx / prev.scale,
          translateY: drag.startTy + dy / prev.scale,
        }));
      } catch { /* prevent crash from propagating to error boundary */ }
    },
    []
  );

  const onPointerUp = useCallback((e: React.PointerEvent) => {
    try {
      pointers.current.delete(e.pointerId);
      if (pointers.current.size < 2) {
        lastPinchDist.current = null;
      }
      if (pointers.current.size === 0) {
        dragStart.current = null;
        setIsPanning(false);
      }
    } catch { /* prevent crash from propagating to error boundary */ }
  }, []);

  const onWheel = useCallback((e: WheelEvent) => {
    try {
      e.preventDefault();
      const container = containerRef.current;
      if (!container) return;

      const rect = container.getBoundingClientRect();
      const cursorX = e.clientX - rect.left;
      const cursorY = e.clientY - rect.top;

      setState((prev) => {
        const direction = e.deltaY > 0 ? -1 : 1;
        const newScale = clampScale(prev.scale + direction * ZOOM_STEP);

        const newTx = cursorX / newScale - cursorX / prev.scale + prev.translateX;
        const newTy = cursorY / newScale - cursorY / prev.scale + prev.translateY;

        return { scale: newScale, translateX: newTx, translateY: newTy };
      });
    } catch { /* prevent crash from propagating to error boundary */ }
  }, []);

  // Attach wheel listener imperatively with { passive: false } so preventDefault() works.
  // React 19 registers onWheel JSX props as passive, which throws on preventDefault().
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      container.removeEventListener("wheel", onWheel);
    };
  }, [onWheel]);

  return {
    containerRef,
    contentRef,
    state,
    isPanning,
    zoomIn,
    zoomOut,
    resetView,
    fitToContainer,
    handlers: {
      onPointerDown,
      onPointerMove,
      onPointerUp,
      onPointerLeave: onPointerUp,
    },
  };
}
