// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChangeEventHandler } from "react";

import ConversationFeed from "@/components/ui/ConversationFeed/ConversationFeed";
import PromptInput from "@/components/ui/PromptInput/PromptInput";
import ChatDisclaimer from "@/features/chat/components/ChatDisclaimer/ChatDisclaimer";
import { ChatTurn } from "@/types";

interface ChatConversationLayoutProps {
  userInput: string;
  conversationTurns: ChatTurn[];
  isChatResponsePending: boolean;
  onPromptChange: ChangeEventHandler<HTMLTextAreaElement>;
  onPromptSubmit: () => void;
  onRequestAbort: () => void;
}

const ChatConversationLayout = ({
  userInput,
  conversationTurns,
  isChatResponsePending,
  onPromptChange,
  onPromptSubmit,
  onRequestAbort,
}: ChatConversationLayoutProps) => (
  <div className="grid h-full grid-rows-[1fr_auto]">
    <ConversationFeed conversationTurns={conversationTurns} />
    <PromptInput
      prompt={userInput}
      isChatResponsePending={isChatResponsePending}
      onRequestAbort={onRequestAbort}
      onChange={onPromptChange}
      onSubmit={onPromptSubmit}
    />
    <ChatDisclaimer />
  </div>
);

export default ChatConversationLayout;
