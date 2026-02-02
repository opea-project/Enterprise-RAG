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
  enableMicrophone?: boolean;
  onPromptChange: ChangeEventHandler<HTMLTextAreaElement>;
  onPromptSubmit: () => void;
  onSpeechToText?: (audioBlob: Blob) => Promise<string>;
  onSpeechToTextError?: (error: Error) => void;
}

export const InitialChatLayout = ({
  userInput,
  disclaimer,
  enableMicrophone = false,
  onPromptChange,
  onPromptSubmit,
  onSpeechToText,
  onSpeechToTextError,
}: InitialChatLayoutProps) => (
  <div className="initial-chat-layout">
    <ChatBotIcon className="initial-chat-layout__chat-bot-icon" />
    <p className="initial-chat-layout__greeting">What do you want to know?</p>
    <PromptInput
      prompt={userInput}
      enableMicrophone={enableMicrophone}
      onChange={onPromptChange}
      onSubmit={onPromptSubmit}
      onSpeechToText={onSpeechToText}
      onSpeechToTextError={onSpeechToTextError}
    />
    <ChatDisclaimer message={disclaimer} />
  </div>
);
