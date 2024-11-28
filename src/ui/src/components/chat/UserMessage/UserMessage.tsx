// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UserMessage.scss";

import ChatMessageMarkdown from "@/components/chat/ChatMessageMarkdown/ChatMessageMarkdown";

interface UserMessageProps {
  text: string;
}

const UserMessage = ({ text }: UserMessageProps) => (
  <div className="user-message">
    <ChatMessageMarkdown text={text} />
  </div>
);

export default UserMessage;
