// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ConversationFeedLayout.scss";

import { ChangeEventHandler } from "react";

import ConversationFeed from "@/components/ui/ConversationFeed/ConversationFeed";
import PromptInput from "@/components/ui/PromptInput/PromptInput";
import ChatDisclaimer from "@/features/chat/components/ChatDisclaimer/ChatDisclaimer";
import { ChatMessage } from "@/types";

interface ConversationFeedLayoutProps {
  messages: ChatMessage[];
  prompt: string;
  isStreaming: boolean;
  abortRequest: () => void;
  onPromptSubmit: () => void;
  onPromptChange: ChangeEventHandler<HTMLTextAreaElement>;
}

const ConversationFeedLayout = ({
  messages,
  prompt,
  isStreaming,
  abortRequest,
  onPromptSubmit,
  onPromptChange,
}: ConversationFeedLayoutProps) => (
  <div className="conversation-feed-layout">
    <ConversationFeed messages={messages} />
    <PromptInput
      prompt={prompt}
      isStreaming={isStreaming}
      abortRequest={abortRequest}
      onChange={onPromptChange}
      onSubmit={onPromptSubmit}
    />
    <ChatDisclaimer />
  </div>
);

export default ConversationFeedLayout;
