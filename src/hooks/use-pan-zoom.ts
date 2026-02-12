"use client";

import { useCallback, useRef, useState } from "react";

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

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });

      if (pointers.current.size === 1) {
        // Single pointer: start drag/pan
        dragStart.current = {
          pointerId: e.pointerId,
          startX: e.clientX,
          startY: e.clientY,
          startTx: state.translateX,
          startTy: state.translateY,
        };
        setIsPanning(true);
        (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
      } else if (pointers.current.size === 2) {
        // Two pointers: init pinch
        const pts = Array.from(pointers.current.values());
        lastPinchDist.current = getDistance(pts[0], pts[1]);
        dragStart.current = null;
        setIsPanning(false);
      }
    },
    [state.translateX, state.translateY]
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });

      if (pointers.current.size === 2 && lastPinchDist.current !== null) {
        // Pinch zoom
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

      if (!dragStart.current || e.pointerId !== dragStart.current.pointerId) return;

      const dx = e.clientX - dragStart.current.startX;
      const dy = e.clientY - dragStart.current.startY;

      setState((prev) => ({
        ...prev,
        translateX: dragStart.current!.startTx + dx / prev.scale,
        translateY: dragStart.current!.startTy + dy / prev.scale,
      }));
    },
    []
  );

  const onPointerUp = useCallback((e: React.PointerEvent) => {
    pointers.current.delete(e.pointerId);
    if (pointers.current.size < 2) {
      lastPinchDist.current = null;
    }
    if (pointers.current.size === 0) {
      dragStart.current = null;
      setIsPanning(false);
    }
  }, []);

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const container = containerRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const cursorX = e.clientX - rect.left;
    const cursorY = e.clientY - rect.top;

    setState((prev) => {
      const direction = e.deltaY > 0 ? -1 : 1;
      const newScale = clampScale(prev.scale + direction * ZOOM_STEP);
      const scaleFactor = newScale / prev.scale;

      // Zoom toward cursor: adjust translate so cursor point stays fixed
      const newTx = cursorX / newScale - cursorX / prev.scale + prev.translateX;
      const newTy = cursorY / newScale - cursorY / prev.scale + prev.translateY;

      return { scale: newScale, translateX: newTx, translateY: newTy };
    });
  }, []);

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
      onWheel,
    },
  };
}
