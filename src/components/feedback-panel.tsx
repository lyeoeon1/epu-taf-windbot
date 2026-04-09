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
    positiveTags: {
      factually_correct: "Factually correct",
      easy_to_understand: "Easy to understand",
      informative: "Informative",
      creative: "Creative / Interesting",
      other: "Khác",
    },
    negativeTags: {
      unsafe: "Phản cảm/không an toàn",
      not_relevant: "Không liên quan",
      not_factual: "Câu trả lời không đúng sự thật",
      partially_incorrect: "Có phần không chính xác",
      other: "Khác",
    },
  },
  en: {
    title: "Provide additional feedback (optional)",
    placeholder: "Share other feedback...",
    cancel: "Cancel",
    submit: "Submit",
    submitted: "Thanks for your feedback!",
    positiveTags: {
      factually_correct: "Factually correct",
      easy_to_understand: "Easy to understand",
      informative: "Informative",
      creative: "Creative / Interesting",
      other: "Other",
    },
    negativeTags: {
      unsafe: "Unsafe / Offensive",
      not_relevant: "Not relevant",
      not_factual: "Not factually correct",
      partially_incorrect: "Partially incorrect",
      other: "Other",
    },
  },
};

const POSITIVE_TAG_KEYS = ["factually_correct", "easy_to_understand", "informative", "creative", "other"] as const;
const NEGATIVE_TAG_KEYS = ["unsafe", "not_relevant", "not_factual", "partially_incorrect", "other"] as const;

interface FeedbackPanelProps {
  sessionId: string | null;
  messageContent: string;
  variant: "positive" | "negative";
  onClose: () => void;
}

export function FeedbackPanel({ sessionId, messageContent, variant, onClose }: FeedbackPanelProps) {
  const { language } = useLanguage();
  const t = labels[language];
  const tagKeys = variant === "positive" ? POSITIVE_TAG_KEYS : NEGATIVE_TAG_KEYS;
  const tagLabels = variant === "positive" ? t.positiveTags : t.negativeTags;
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
          feedback_tags: [`vote_${variant}`, ...Array.from(selectedTags)],
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
  }, [selectedTags, feedbackText, sessionId, messageContent, variant, onClose]);

  if (submitted) {
    return (
      <div className="rounded-xl px-4 py-3 text-xs text-green-700 dark:bg-[#262626] dark:text-green-400">
        {t.submitted}
      </div>
    );
  }

  return (
    <div className="rounded-xl p-4 dark:bg-[#262626]">
      <p className="mb-2 text-xs font-medium text-muted-foreground dark:text-gray-400">
        {t.title}
      </p>

      <div className="mb-2 flex flex-wrap gap-1.5">
        {tagKeys.map((tag) => (
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
            {tagLabels[tag as keyof typeof tagLabels]}
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
