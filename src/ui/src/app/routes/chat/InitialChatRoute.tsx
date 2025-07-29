// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import PageLayout from "@/components/layouts/PageLayout/PageLayout";
import ChatSideMenu from "@/features/chat/components/ChatSideMenu/ChatSideMenu";
import ChatSideMenuIconButton from "@/features/chat/components/ChatSideMenuIconButton/ChatSideMenuIconButton";
import useChat from "@/features/chat/hooks/useChat";
import ChatConversationLayout from "@/features/chat/layouts/ChatConversationLayout/ChatConversationLayout";
import InitialChatLayout from "@/features/chat/layouts/InitialChatLayout/InitialChatLayout";

const InitialChatRoute = () => {
  const {
    userInput,
    chatTurns,
    isChatHistorySideMenuOpen,
    isChatResponsePending,
    onPromptChange,
    onPromptSubmit,
    onRequestAbort,
  } = useChat();

  const getChatLayout = () => {
    if (chatTurns.length === 0) {
      return (
        <InitialChatLayout
          userInput={userInput}
          onPromptChange={onPromptChange}
          onPromptSubmit={onPromptSubmit}
        />
      );
    }

    return (
      <ChatConversationLayout
        userInput={userInput}
        conversationTurns={chatTurns}
        isChatResponsePending={isChatResponsePending}
        onPromptChange={onPromptChange}
        onPromptSubmit={onPromptSubmit}
        onRequestAbort={onRequestAbort}
      />
    );
  };

  return (
    <PageLayout
      appHeaderProps={{
        leftSideMenuTrigger: <ChatSideMenuIconButton />,
      }}
      leftSideMenu={{
        component: <ChatSideMenu />,
        isOpen: isChatHistorySideMenuOpen,
      }}
    >
      {getChatLayout()}
    </PageLayout>
  );
};

export default InitialChatRoute;
