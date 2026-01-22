// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PageLayout } from "@intel-enterprise-rag-ui/layouts";

import {
  AppHeaderLeftSideContent,
  AppHeaderRightSideContent,
} from "@/components/AppHeaderContent/AppHeaderContent";
import ChatSideMenu from "@/features/chat/components/ChatSideMenu/ChatSideMenu";
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
        leftSideContent: <AppHeaderLeftSideContent />,
        rightSideContent: <AppHeaderRightSideContent />,
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
