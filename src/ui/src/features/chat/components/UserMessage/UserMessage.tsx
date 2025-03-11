// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UserMessage.scss";

import ChatMessageMarkdown from "@/features/chat/components/ChatMessageMarkdown/ChatMessageMarkdown";

interface UserMessageProps {
  text: string;
}

const UserMessage = ({ text }: UserMessageProps) => (
  <article className="user-message">
    <div className="user-message__text">
      <ChatMessageMarkdown text={text} />
    </div>
  </article>
);

export default UserMessage;
