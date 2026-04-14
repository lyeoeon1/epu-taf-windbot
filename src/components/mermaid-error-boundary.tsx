"use client";

import React from "react";

interface Props {
  code: string;
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
}

export class MermaidErrorBoundary extends React.Component<Props, State> {
  private recoverTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidUpdate(prevProps: Props) {
    // Reset error state when code changes so diagram can re-render
    if (prevProps.code !== this.props.code && this.state.hasError) {
      this.clearRecoverTimer();
      this.setState({ hasError: false });
    }
    // Auto-recover from interaction errors after 1s (even if code hasn't changed)
    if (this.state.hasError && !this.recoverTimer) {
      this.recoverTimer = setTimeout(() => {
        this.recoverTimer = null;
        this.setState({ hasError: false });
      }, 1000);
    }
  }

  componentWillUnmount() {
    this.clearRecoverTimer();
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("MermaidBlock error:", error, errorInfo);
  }

  private clearRecoverTimer() {
    if (this.recoverTimer) {
      clearTimeout(this.recoverTimer);
      this.recoverTimer = null;
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <pre className="mermaid-error">
          <code>{this.props.code}</code>
        </pre>
      );
    }
    return this.props.children;
  }
}
