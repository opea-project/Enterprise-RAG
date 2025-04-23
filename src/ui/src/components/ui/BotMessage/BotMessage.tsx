// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./BotMessage.scss";

import { memo } from "react";

import ChatBotIcon from "@/components/icons/ChatBotIcon/ChatBotIcon";
import ErrorIcon from "@/components/icons/ErrorIcon/ErrorIcon";
import MarkdownRenderer from "@/components/markdown/MarkdownRenderer";
import PulsingDot from "@/components/ui/PulsingDot/PulsingDot";
import { ConversationTurn } from "@/types";
import { sanitizeString } from "@/utils";

type BotMessageProps = Pick<ConversationTurn, "answer" | "error" | "isPending">;

const BotMessage = memo(({ answer, error, isPending }: BotMessageProps) => {
  const isWaitingForAnswer = isPending && (answer === "" || error !== null);
  const sanitizedAnswer = sanitizeString(answer);

  const botResponse =
    error !== null ? (
      <div className="bot-message__error">
        <ErrorIcon />
        <p>{error}</p>
      </div>
    ) : (
      <div className="bot-message__text">
        <MarkdownRenderer content={sanitizedAnswer} />
      </div>
    );

  return (
    <div className="bot-message">
      <ChatBotIcon forConversation />
      {isWaitingForAnswer ? <PulsingDot /> : botResponse}
    </div>
  );
});

export default BotMessage;
