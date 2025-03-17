// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ConversationFeedLayout from "@/features/chat/layouts/ConversationFeedLayout/ConversationFeedLayout";
import InitialChatLayout from "@/features/chat/layouts/InitialChatLayout/InitialChatLayout";
import { selectMessages } from "@/features/chat/store/conversationFeed.slice";
import { useAppSelector } from "@/store/hooks";

const ChatRoute = () => {
  const messages = useAppSelector(selectMessages);

  if (messages.length === 0) {
    return <InitialChatLayout />;
  }

  return <ConversationFeedLayout />;
};

export default ChatRoute;
