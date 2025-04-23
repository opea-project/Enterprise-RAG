// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import useChat from "@/features/chat/hooks/useChat";
import ConversationFeedLayout from "@/features/chat/layouts/ConversationFeedLayout/ConversationFeedLayout";
import InitialChatLayout from "@/features/chat/layouts/InitialChatLayout/InitialChatLayout";

const ChatRoute = () => {
  const {
    userInput,
    conversationTurns,
    isChatResponsePending,
    onPromptChange,
    onPromptSubmit,
    onRequestAbort,
  } = useChat();

  if (conversationTurns.length === 0) {
    return (
      <InitialChatLayout
        userInput={userInput}
        isChatResponsePending={isChatResponsePending}
        onPromptChange={onPromptChange}
        onPromptSubmit={onPromptSubmit}
        onRequestAbort={onRequestAbort}
      />
    );
  }

  return (
    <ConversationFeedLayout
      userInput={userInput}
      conversationTurns={conversationTurns}
      isChatResponsePending={isChatResponsePending}
      onPromptChange={onPromptChange}
      onPromptSubmit={onPromptSubmit}
      onRequestAbort={onRequestAbort}
    />
  );
};

export default ChatRoute;
