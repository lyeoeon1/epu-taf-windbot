"use client";

import { useCallback, useState } from "react";

const TITLE = "Phản hồi thêm (không bắt buộc) / Additional feedback (optional)";
const PLACEHOLDER = "Nhập ý kiến... / Your feedback...";
const CANCEL = "Hủy";
const SUBMIT = "Gửi";
const SUBMITTED = "Cảm ơn phản hồi! / Thanks for your feedback!";

const POSITIVE_TAGS = {
  factually_correct: "Chính xác / Factually correct",
  easy_to_understand: "Dễ hiểu / Easy to understand",
  informative: "Hữu ích / Informative",
  creative: "Sáng tạo / Creative",
  other: "Khác / Other",
} as const;

const NEGATIVE_TAGS = {
  unsafe: "Không an toàn / Unsafe",
  not_relevant: "Không liên quan / Not relevant",
  not_factual: "Sai sự thật / Not factual",
  partially_incorrect: "Chưa chính xác / Partially incorrect",
  other: "Khác / Other",
} as const;

const POSITIVE_TAG_KEYS = Object.keys(POSITIVE_TAGS) as (keyof typeof POSITIVE_TAGS)[];
const NEGATIVE_TAG_KEYS = Object.keys(NEGATIVE_TAGS) as (keyof typeof NEGATIVE_TAGS)[];

interface FeedbackPanelProps {
  sessionId: string | null;
  messageContent: string;
  variant: "positive" | "negative";
  onClose: () => void;
}

export function FeedbackPanel({ sessionId, messageContent, variant, onClose }: FeedbackPanelProps) {
  const tagKeys = variant === "positive" ? POSITIVE_TAG_KEYS : NEGATIVE_TAG_KEYS;
  const tagLabels = variant === "positive" ? POSITIVE_TAGS : NEGATIVE_TAGS;
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
      <div className="max-w-sm rounded-xl px-4 py-3 text-[13px] text-green-700 shadow-lg dark:bg-[#262626] dark:text-green-400">
        {SUBMITTED}
      </div>
    );
  }

  return (
    <div className="max-w-sm rounded-xl p-4 shadow-lg dark:bg-[#262626]">
      <p className="mb-3 text-[13px] font-medium text-muted-foreground dark:text-gray-400">
        {TITLE}
      </p>

      <div className="mb-3 flex flex-wrap gap-2">
        {tagKeys.map((tag) => (
          <button
            key={tag}
            type="button"
            onClick={() => toggleTag(tag)}
            className={`cursor-pointer rounded-full border px-3 py-1.5 text-[13px] transition-colors ${
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
        placeholder={PLACEHOLDER}
        rows={3}
        className="mb-3 w-full resize-none rounded-md border border-gray-200 bg-white px-3 py-2 text-[13px] text-foreground placeholder:text-muted-foreground focus:border-blue-400 focus:outline-none dark:border-[#515151] dark:bg-[#303030] dark:text-white dark:placeholder:text-gray-500 dark:focus:border-blue-500"
      />

      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          className="cursor-pointer rounded-md px-3 py-1.5 text-[13px] text-muted-foreground transition-colors hover:bg-accent dark:text-gray-400 dark:hover:bg-[#515151]"
        >
          {CANCEL}
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting || (selectedTags.size === 0 && !feedbackText.trim())}
          className="cursor-pointer rounded-md bg-blue-600 px-3 py-1.5 text-[13px] text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
        >
          {submitting ? "..." : SUBMIT}
        </button>
      </div>
    </div>
  );
}
