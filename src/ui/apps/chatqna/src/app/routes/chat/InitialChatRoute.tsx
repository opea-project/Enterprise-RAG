// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PageLayout } from "@intel-enterprise-rag-ui/layouts";

import {
  AppHeaderLeftSideContent,
  AppHeaderRightSideContent,
} from "@/components/AppHeaderContent/AppHeaderContent";
import ChatSideMenu from "@/features/chat/components/ChatSideMenu/ChatSideMenu";
import useInitialChat from "@/features/chat/hooks/useInitialChat";
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
  } = useInitialChat();

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
        leftSideContent: <AppHeaderLeftSideContent />,
        rightSideContent: <AppHeaderRightSideContent />,
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
