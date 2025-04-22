// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./BotMessage.scss";

import ChatBotIcon from "@/components/icons/ChatBotIcon/ChatBotIcon";
import ErrorIcon from "@/components/icons/ErrorIcon/ErrorIcon";
import MarkdownRenderer from "@/components/markdown/MarkdownRenderer";
import PulsingDot from "@/components/ui/PulsingDot/PulsingDot";
import { ChatMessage } from "@/types";
import { sanitizeString } from "@/utils";

type BotMessageProps = Pick<ChatMessage, "text" | "isStreaming" | "isError">;

const BotMessage = ({ text, isStreaming, isError }: BotMessageProps) => {
  const isWaitingForMessage = isStreaming && text === "";
  const sanitizedMessage = sanitizeString(text);

  const botMessage = isError ? (
    <div className="bot-message__error">
      <ErrorIcon />
      <p>{sanitizedMessage}</p>
    </div>
  ) : (
    <div className="bot-message__text">
      <MarkdownRenderer content={sanitizedMessage} />
    </div>
  );

  return (
    <div className="bot-message">
      <ChatBotIcon forConversation />
      {isWaitingForMessage && <PulsingDot />}
      {sanitizedMessage !== "" && botMessage}
    </div>
  );
};

export default BotMessage;
