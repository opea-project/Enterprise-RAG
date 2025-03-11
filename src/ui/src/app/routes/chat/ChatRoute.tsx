// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatRoute.scss";

import ChatBotIcon from "@/components/icons/ChatBotIcon/ChatBotIcon";
import ChatDisclaimer from "@/features/chat/components/ChatDisclaimer/ChatDisclaimer";
import ConversationFeed from "@/features/chat/components/ConversationFeed/ConversationFeed";
import PromptInput from "@/features/chat/components/PromptInput/PromptInput";
import { selectMessages } from "@/features/chat/store/conversationFeed.slice";
import { useAppSelector } from "@/store/hooks";

const ChatRoute = () => {
  const messages = useAppSelector(selectMessages);

  if (messages.length === 0) {
    return (
      <div className="chat-page--no-messages">
        <ChatBotIcon />
        <p className="chat-page__greeting">What do you want to know?</p>
        <PromptInput />
        <ChatDisclaimer />
      </div>
    );
  }

  return (
    <div className="chat-page">
      <ConversationFeed />
      <PromptInput />
      <ChatDisclaimer />
    </div>
  );
};

export default ChatRoute;
