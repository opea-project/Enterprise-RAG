// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import useChat from "@/features/chat/hooks/useChat";
import ConversationFeedLayout from "@/features/chat/layouts/ConversationFeedLayout/ConversationFeedLayout";
import InitialChatLayout from "@/features/chat/layouts/InitialChatLayout/InitialChatLayout";

const ChatRoute = () => {
  const {
    messages,
    prompt,
    isStreaming,
    abortRequest,
    onPromptSubmit,
    onPromptChange,
  } = useChat();

  if (messages.length === 0) {
    return (
      <InitialChatLayout
        prompt={prompt}
        isStreaming={isStreaming}
        abortRequest={abortRequest}
        onPromptSubmit={onPromptSubmit}
        onPromptChange={onPromptChange}
      />
    );
  }

  return (
    <ConversationFeedLayout
      messages={messages}
      prompt={prompt}
      isStreaming={isStreaming}
      abortRequest={abortRequest}
      onPromptSubmit={onPromptSubmit}
      onPromptChange={onPromptChange}
    />
  );
};

export default ChatRoute;
