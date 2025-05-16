// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import PageLayout from "@/components/layouts/PageLayout/PageLayout";
import NewChatButton from "@/features/chat/components/NewChatButton/NewChatButton";
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
    onNewChat,
  } = useChat();

  const getChatLayout = () => {
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

  return (
    <PageLayout appHeaderExtraActions={<NewChatButton onNewChat={onNewChat} />}>
      {getChatLayout()}
    </PageLayout>
  );
};

export default ChatRoute;
