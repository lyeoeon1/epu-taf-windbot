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
      this.setState({ hasError: false });
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("MermaidBlock error:", error, errorInfo);
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
