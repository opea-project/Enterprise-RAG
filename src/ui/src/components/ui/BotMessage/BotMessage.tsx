// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./BotMessage.scss";

import classNames from "classnames";
import { memo } from "react";

import ChatBotIcon from "@/components/icons/ChatBotIcon/ChatBotIcon";
import ErrorIcon from "@/components/icons/ErrorIcon/ErrorIcon";
import MarkdownRenderer from "@/components/markdown/MarkdownRenderer";
import CopyButton from "@/components/ui/CopyButton/CopyButton";
import PulsingDot from "@/components/ui/PulsingDot/PulsingDot";
import SourcesGrid from "@/features/chat/components/SourcesGrid/SourcesGrid";
import { ChatTurn } from "@/types";
import { sanitizeString } from "@/utils";

type BotMessageProps = Pick<
  ChatTurn,
  "answer" | "error" | "isPending" | "sources"
>;

const BotMessage = memo(
  ({ answer, error, isPending, sources }: BotMessageProps) => {
    const isWaitingForAnswer = isPending && (answer === "" || error !== null);
    const sanitizedAnswer = sanitizeString(answer);
    const showActions =
      !isPending && (sanitizedAnswer !== "" || error !== null);
    const showSources = showActions && Array.isArray(sources);

    const botResponse =
      error !== null ? (
        <div className="bot-message__error">
          <ErrorIcon />
          <p>{error}</p>
        </div>
      ) : (
        <div className="bot-message__text">
          <MarkdownRenderer content={sanitizedAnswer} />
          {showActions && (
            <footer className="bot-message__footer">
              <CopyButton textToCopy={sanitizedAnswer} />
            </footer>
          )}
          {showSources && <SourcesGrid sources={sources} />}
        </div>
      );

    const className = classNames("bot-message", {
      "mb-6": isWaitingForAnswer,
      "mb-4": !isWaitingForAnswer,
    });

    return (
      <div className={className}>
        <ChatBotIcon forConversation />
        {isWaitingForAnswer ? <PulsingDot /> : botResponse}
      </div>
    );
  },
);

export default BotMessage;
