// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UserMessage.scss";

import ChatMessageMarkdown from "@/components/ui/ChatMessageMarkdown/ChatMessageMarkdown";
import { ChatMessage } from "@/types";

type UserMessageProps = Pick<ChatMessage, "text">;

const UserMessage = ({ text }: UserMessageProps) => (
  <article className="user-message">
    <div className="user-message__text">
      <ChatMessageMarkdown text={text} />
    </div>
  </article>
);

export default UserMessage;
