// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatMessage.scss";

import classNames from "classnames";

import ChatMessageAvatar from "@/components/chat/ChatMessageAvatar/ChatMessageAvatar";
import ChatMessageMarkdown from "@/components/chat/ChatMessageMarkdown/ChatMessageMarkdown";

interface ChatMessageProps {
  text: string;
  isUserMessage: boolean;
}

const ChatMessage = ({ text, isUserMessage }: ChatMessageProps) => (
  <div
    className={classNames({
      "chat-message": true,
      "chat-user-message": isUserMessage,
    })}
  >
    <ChatMessageAvatar isUserMessage={isUserMessage} />
    <div>
      <ChatMessageMarkdown text={text} />
    </div>
  </div>
);

export default ChatMessage;
