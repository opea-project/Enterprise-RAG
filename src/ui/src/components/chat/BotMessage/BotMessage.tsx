// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./BotMessage.scss";

import ChatIcon from "@/components/chat/ChatIcon/ChatIcon";
import ChatMessageMarkdown from "@/components/chat/ChatMessageMarkdown/ChatMessageMarkdown";
import PulsingDot from "@/components/chat/PulsingDot/PulsingDot";
import { sanitizeString } from "@/utils";

interface BotMessageProps {
  text: string;
  isStreaming?: boolean;
}

const BotMessage = ({ text, isStreaming }: BotMessageProps) => {
  const isWaitingForMessage = isStreaming && text === "";
  const sanitizedMessage = sanitizeString(text);

  return (
    <div className="bot-message">
      <ChatIcon forConversation />
      {isWaitingForMessage && <PulsingDot />}
      {sanitizedMessage !== "" && (
        <div className="bot-message__text">
          <ChatMessageMarkdown text={sanitizedMessage} />
        </div>
      )}
    </div>
  );
};

export default BotMessage;
