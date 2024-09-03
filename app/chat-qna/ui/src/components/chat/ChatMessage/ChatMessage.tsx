// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatMessage.scss";

import ChatMessageAvatar from "@/components/chat/ChatMessageAvatar/ChatMessageAvatar";
import ChatMessageMarkdown from "@/components/chat/ChatMessageMarkdown/ChatMessageMarkdown";

interface ChatMessageProps {
  text: string;
  isUserMessage: boolean;
}

const ChatMessage = ({ text, isUserMessage }: ChatMessageProps) => (
  <div className={`message ${isUserMessage ? "" : "bot-message"}`}>
    <ChatMessageAvatar isUserMessage={isUserMessage} />
    <ChatMessageMarkdown text={text} />
  </div>
);

export default ChatMessage;
