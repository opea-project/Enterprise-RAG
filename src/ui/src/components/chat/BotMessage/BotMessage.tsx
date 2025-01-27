// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./BotMessage.scss";

import { BsExclamationCircleFill } from "react-icons/bs";

import ChatIcon from "@/components/chat/ChatIcon/ChatIcon";
import ChatMessageMarkdown from "@/components/chat/ChatMessageMarkdown/ChatMessageMarkdown";
import PulsingDot from "@/components/chat/PulsingDot/PulsingDot";
import { sanitizeString } from "@/utils";

interface BotMessageProps {
  text: string;
  isStreaming?: boolean;
  isError?: boolean;
}

const BotMessage = ({ text, isStreaming, isError }: BotMessageProps) => {
  const isWaitingForMessage = isStreaming && text === "";
  const sanitizedMessage = sanitizeString(text);

  const botMessage = isError ? (
    <div className="bot-message__error">
      <BsExclamationCircleFill />
      <p>{sanitizedMessage}</p>
    </div>
  ) : (
    <div className="bot-message__text">
      <ChatMessageMarkdown text={sanitizedMessage} />
    </div>
  );

  return (
    <div className="bot-message">
      <ChatIcon forConversation />
      {isWaitingForMessage && <PulsingDot />}
      {sanitizedMessage !== "" && botMessage}
    </div>
  );
};

export default BotMessage;
