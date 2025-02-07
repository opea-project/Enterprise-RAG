// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatPage.scss";

import ChatDisclaimer from "@/components/chat/ChatDisclaimer/ChatDisclaimer";
import ConversationFeed from "@/components/chat/ConversationFeed/ConversationFeed";
import PromptInput from "@/components/chat/PromptInput/PromptInput";
import ChatBotIcon from "@/components/icons/ChatBotIcon/ChatBotIcon";
import { selectMessages } from "@/store/conversationFeed.slice";
import { useAppSelector } from "@/store/hooks";

const ChatPage = () => {
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

export default ChatPage;
