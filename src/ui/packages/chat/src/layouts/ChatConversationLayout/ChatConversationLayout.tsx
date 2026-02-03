// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatConversationLayout.scss";

import { ChangeEventHandler } from "react";

import { ChatDisclaimer } from "@/components/conversation-feed/ChatDisclaimer/ChatDisclaimer";
import { ConversationFeed } from "@/components/conversation-feed/ConversationFeed/ConversationFeed";
import { PlaySpeechButtonState } from "@/components/conversation-feed/PlaySpeechButton/PlaySpeechButton";
import { PromptInput } from "@/components/conversation-feed/PromptInput/PromptInput";
import { ChatTurn } from "@/types";

interface ChatConversationLayoutProps {
  userInput: string;
  conversationTurns: ChatTurn[];
  isChatResponsePending: boolean;
  disclaimer: string;
  playingState?: PlaySpeechButtonState;
  playingTurnId?: string | null;
  enableMicrophone?: boolean;
  onPromptChange: ChangeEventHandler<HTMLTextAreaElement>;
  onPromptSubmit: () => void;
  onRequestAbort: () => void;
  onFileDownload: (fileName: string, bucketName: string) => void;
  onPlayMessage?: (turnId: string) => Promise<void>;
  onSpeechToText?: (audioBlob: Blob) => Promise<string>;
  onSpeechToTextError?: (error: Error) => void;
}

export const ChatConversationLayout = ({
  userInput,
  conversationTurns,
  isChatResponsePending,
  disclaimer,
  playingState,
  playingTurnId,
  enableMicrophone = false,
  onPromptChange,
  onPromptSubmit,
  onRequestAbort,
  onFileDownload,
  onPlayMessage,
  onSpeechToText,
  onSpeechToTextError,
}: ChatConversationLayoutProps) => (
  <div className="chat-conversation-layout">
    <ConversationFeed
      conversationTurns={conversationTurns}
      playingState={playingState}
      playingTurnId={playingTurnId}
      onFileDownload={onFileDownload}
      onPlayMessage={onPlayMessage}
    />
    <PromptInput
      prompt={userInput}
      isChatResponsePending={isChatResponsePending}
      enableMicrophone={enableMicrophone}
      onRequestAbort={onRequestAbort}
      onChange={onPromptChange}
      onSubmit={onPromptSubmit}
      onSpeechToText={onSpeechToText}
      onSpeechToTextError={onSpeechToTextError}
    />
    <ChatDisclaimer message={disclaimer} />
  </div>
);
