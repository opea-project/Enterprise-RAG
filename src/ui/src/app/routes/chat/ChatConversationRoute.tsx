// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import PageLayout from "@/components/layouts/PageLayout/PageLayout";
import ChatSideMenu from "@/features/chat/components/ChatSideMenu/ChatSideMenu";
import ChatSideMenuIconButton from "@/features/chat/components/ChatSideMenuIconButton/ChatSideMenuIconButton";
import NewChatButton from "@/features/chat/components/NewChatButton/NewChatButton";
import useChat from "@/features/chat/hooks/useChat";
import ChatConversationLayout from "@/features/chat/layouts/ChatConversationLayout/ChatConversationLayout";

const ChatConversationRoute = () => {
  const {
    userInput,
    chatTurns,
    isChatResponsePending,
    isChatHistorySideMenuOpen,
    onPromptChange,
    onPromptSubmit,
    onRequestAbort,
  } = useChat();

  return (
    <PageLayout
      appHeaderProps={{
        leftSideMenuTrigger: <ChatSideMenuIconButton />,
        extraActions: <NewChatButton />,
      }}
      leftSideMenu={{
        component: <ChatSideMenu />,
        isOpen: isChatHistorySideMenuOpen,
      }}
    >
      <ChatConversationLayout
        userInput={userInput}
        conversationTurns={chatTurns}
        isChatResponsePending={isChatResponsePending}
        onPromptChange={onPromptChange}
        onPromptSubmit={onPromptSubmit}
        onRequestAbort={onRequestAbort}
      />
    </PageLayout>
  );
};

export default ChatConversationRoute;
