// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChangeEventHandler } from "react";

import { ChatDisclaimer } from "@/components/conversation-feed/ChatDisclaimer/ChatDisclaimer";
import { ConversationFeed } from "@/components/conversation-feed/ConversationFeed/ConversationFeed";
import { PromptInput } from "@/components/conversation-feed/PromptInput/PromptInput";
import { ChatTurn } from "@/types";

interface ChatConversationLayoutProps {
  userInput: string;
  conversationTurns: ChatTurn[];
  isChatResponsePending: boolean;
  disclaimer: string;
  onPromptChange: ChangeEventHandler<HTMLTextAreaElement>;
  onPromptSubmit: () => void;
  onRequestAbort: () => void;
  onFileDownload: (fileName: string, bucketName: string) => void;
}

export const ChatConversationLayout = ({
  userInput,
  conversationTurns,
  isChatResponsePending,
  disclaimer,
  onPromptChange,
  onPromptSubmit,
  onRequestAbort,
  onFileDownload,
}: ChatConversationLayoutProps) => (
  <div className="grid h-full grid-rows-[1fr_auto]">
    <ConversationFeed
      conversationTurns={conversationTurns}
      onFileDownload={onFileDownload}
    />
    <PromptInput
      prompt={userInput}
      isChatResponsePending={isChatResponsePending}
      onRequestAbort={onRequestAbort}
      onChange={onPromptChange}
      onSubmit={onPromptSubmit}
    />
    <ChatDisclaimer message={disclaimer} />
  </div>
);
