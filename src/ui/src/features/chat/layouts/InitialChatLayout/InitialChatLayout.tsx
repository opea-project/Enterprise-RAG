// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./InitialChatLayout.scss";

import { ChangeEventHandler } from "react";

import ChatBotIcon from "@/components/icons/ChatBotIcon/ChatBotIcon";
import PromptInput from "@/components/ui/PromptInput/PromptInput";
import ChatDisclaimer from "@/features/chat/components/ChatDisclaimer/ChatDisclaimer";

interface InitialChatLayoutProps {
  userInput: string;
  onPromptChange: ChangeEventHandler<HTMLTextAreaElement>;
  onPromptSubmit: () => void;
}

const InitialChatLayout = ({
  userInput,
  onPromptChange,
  onPromptSubmit,
}: InitialChatLayoutProps) => (
  <div className="initial-chat-layout">
    <ChatBotIcon />
    <p className="initial-chat-layout__greeting">What do you want to know?</p>
    <PromptInput
      prompt={userInput}
      onChange={onPromptChange}
      onSubmit={onPromptSubmit}
    />
    <ChatDisclaimer />
  </div>
);

export default InitialChatLayout;
