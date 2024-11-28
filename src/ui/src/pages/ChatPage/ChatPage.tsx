// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatPage.scss";

import ChatIcon from "@/components/chat/ChatIcon/ChatIcon";
import ConversationFeed from "@/components/chat/ConversationFeed/ConversationFeed";
import PromptInput from "@/components/chat/PromptInput/PromptInput";
import { selectMessages } from "@/store/conversationFeed.slice";
import { useAppSelector } from "@/store/hooks";

const ChatPage = () => {
  const messages = useAppSelector(selectMessages);

  if (messages.length === 0) {
    return (
      <div className="chat-page--no-messages">
        <ChatIcon />
        <p className="chat-page__greeting">What do you want to know?</p>
        <PromptInput />
      </div>
    );
  }
  return (
    <div className="chat-page">
      <ConversationFeed />
      <PromptInput />
    </div>
  );
};

export default ChatPage;
