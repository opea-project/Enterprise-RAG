// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./InitialChatLayout.scss";

import { ChatBotIcon } from "@intel-enterprise-rag-ui/icons";
import { ChangeEventHandler } from "react";

import { ChatDisclaimer } from "@/components/conversation-feed/ChatDisclaimer/ChatDisclaimer";
import { PromptInput } from "@/components/conversation-feed/PromptInput/PromptInput";

interface InitialChatLayoutProps {
  userInput: string;
  disclaimer: string;
  onPromptChange: ChangeEventHandler<HTMLTextAreaElement>;
  onPromptSubmit: () => void;
}

export const InitialChatLayout = ({
  userInput,
  disclaimer,
  onPromptChange,
  onPromptSubmit,
}: InitialChatLayoutProps) => (
  <div className="initial-chat-layout">
    <ChatBotIcon className="initial-chat-layout__chat-bot-icon" />
    <p className="initial-chat-layout__greeting">What do you want to know?</p>
    <PromptInput
      prompt={userInput}
      onChange={onPromptChange}
      onSubmit={onPromptSubmit}
    />
    <ChatDisclaimer message={disclaimer} />
  </div>
);
