"use client";

import { PromptBox } from "@/components/prompt-box";

export default function Home() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-background dark:bg-[#212121] px-4">
      <div className="flex w-full max-w-2xl flex-col items-center gap-8">
        <div className="text-center">
          <h1 className="text-3xl font-semibold text-foreground dark:text-white">
            What can I help with?
          </h1>
        </div>
        <div className="w-full">
          <PromptBox />
        </div>
      </div>
    </div>
  );
}
