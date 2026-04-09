"use client";

import { useCallback, useState } from "react";
import { useLanguage } from "@/contexts/language-context";

const labels = {
  vi: {
    title: "Cung cấp thêm phản hồi (không bắt buộc)",
    placeholder: "Cung cấp ý kiến phản hồi khác...",
    cancel: "Hủy",
    submit: "Gửi",
    submitted: "Cảm ơn phản hồi!",
    tags: {
      factually_correct: "Chính xác",
      easy_to_understand: "Dễ hiểu",
      informative: "Hữu ích",
      creative: "Thú vị",
      incorrect: "Không chính xác",
    },
  },
  en: {
    title: "Provide additional feedback (optional)",
    placeholder: "Share other feedback...",
    cancel: "Cancel",
    submit: "Submit",
    submitted: "Thanks for your feedback!",
    tags: {
      factually_correct: "Factually correct",
      easy_to_understand: "Easy to understand",
      informative: "Informative",
      creative: "Creative / Interesting",
      incorrect: "Incorrect",
    },
  },
};

const TAG_KEYS = ["factually_correct", "easy_to_understand", "informative", "creative", "incorrect"] as const;

interface FeedbackPanelProps {
  sessionId: string | null;
  messageContent: string;
  onClose: () => void;
}

export function FeedbackPanel({ sessionId, messageContent, onClose }: FeedbackPanelProps) {
  const { language } = useLanguage();
  const t = labels[language];
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [feedbackText, setFeedbackText] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const toggleTag = useCallback((tag: string) => {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) {
        next.delete(tag);
      } else {
        next.add(tag);
      }
      return next;
    });
  }, []);

  const handleSubmit = useCallback(async () => {
    if (selectedTags.size === 0 && !feedbackText.trim()) return;
    if (!sessionId) return;

    setSubmitting(true);
    try {
      await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message_content: messageContent.slice(0, 2000),
          feedback_tags: Array.from(selectedTags),
          feedback_text: feedbackText.trim(),
        }),
      });
      setSubmitted(true);
      setTimeout(() => onClose(), 1500);
    } catch {
      // Silently fail — feedback is optional
    } finally {
      setSubmitting(false);
    }
  }, [selectedTags, feedbackText, sessionId, messageContent, onClose]);

  if (submitted) {
    return (
      <div className="mt-2 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-xs text-green-700 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400">
        {t.submitted}
      </div>
    );
  }

  return (
    <div className="mt-2 rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-[#414141] dark:bg-[#262626]">
      <p className="mb-2 text-xs font-medium text-muted-foreground dark:text-gray-400">
        {t.title}
      </p>

      <div className="mb-2 flex flex-wrap gap-1.5">
        {TAG_KEYS.map((tag) => (
          <button
            key={tag}
            type="button"
            onClick={() => toggleTag(tag)}
            className={`cursor-pointer rounded-full border px-2.5 py-1 text-xs transition-colors ${
              selectedTags.has(tag)
                ? "border-blue-400 bg-blue-50 text-blue-700 dark:border-blue-500 dark:bg-blue-900/30 dark:text-blue-300"
                : "border-gray-200 text-muted-foreground hover:bg-accent dark:border-[#515151] dark:text-gray-400 dark:hover:bg-[#515151]"
            }`}
          >
            {t.tags[tag as keyof typeof t.tags]}
          </button>
        ))}
      </div>

      <textarea
        value={feedbackText}
        onChange={(e) => setFeedbackText(e.target.value)}
        placeholder={t.placeholder}
        rows={2}
        className="mb-2 w-full resize-none rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:border-blue-400 focus:outline-none dark:border-[#515151] dark:bg-[#303030] dark:text-white dark:placeholder:text-gray-500 dark:focus:border-blue-500"
      />

      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          className="cursor-pointer rounded-md px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent dark:text-gray-400 dark:hover:bg-[#515151]"
        >
          {t.cancel}
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting || (selectedTags.size === 0 && !feedbackText.trim())}
          className="cursor-pointer rounded-md bg-blue-600 px-3 py-1 text-xs text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
        >
          {submitting ? "..." : t.submit}
        </button>
      </div>
    </div>
  );
}
