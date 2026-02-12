"use client";

import { ChatMessages } from "@/components/chat-messages";
import { Header } from "@/components/header";
import { PromptBox } from "@/components/prompt-box";
import { useChat } from "@/hooks/use-chat";
import { useLanguage } from "@/contexts/language-context";

const labels = {
  vi: { greeting: "Tôi có thể giúp gì cho bạn?" },
  en: { greeting: "What can I help with?" },
};

export default function Home() {
  const { language } = useLanguage();
  const t = labels[language];
  const { messages, isLoading, sendMessage, clearChat } = useChat(language);

  if (messages.length === 0) {
    return (
      <div className="flex min-h-svh flex-col bg-background dark:bg-[#212121]">
        <Header onClearChat={clearChat} />
        <div className="flex flex-1 flex-col items-center justify-center px-4">
          <div className="flex w-full max-w-2xl flex-col items-center gap-8">
            <div className="text-center">
              <h1 className="text-3xl font-semibold text-foreground dark:text-white">
                {t.greeting}
              </h1>
            </div>
            <div className="w-full">
              <PromptBox onSend={sendMessage} disabled={isLoading} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-svh flex-col bg-background dark:bg-[#212121]">
      <Header onClearChat={clearChat} />
      <div className="flex-1 overflow-y-auto px-4">
        <div className="mx-auto max-w-2xl py-8">
          <ChatMessages messages={messages} isLoading={isLoading} onSendMessage={sendMessage} />
        </div>
      </div>
      <div className="sticky bottom-0 bg-background dark:bg-[#212121] px-4 pb-4 pt-2">
        <div className="mx-auto max-w-2xl">
          <PromptBox onSend={sendMessage} disabled={isLoading} />
        </div>
      </div>
    </div>
  );
}
