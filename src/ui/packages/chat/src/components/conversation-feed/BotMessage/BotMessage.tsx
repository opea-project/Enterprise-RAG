// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./BotMessage.scss";

import { CopyButton } from "@intel-enterprise-rag-ui/components";
import { ChatBotIcon, ErrorIcon } from "@intel-enterprise-rag-ui/icons";
import { Markdown } from "@intel-enterprise-rag-ui/markdown";
import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import classNames from "classnames";
import { memo } from "react";

import { PulsingDot } from "@/components/conversation-feed/PulsingDot/PulsingDot";
import { SourcesGrid } from "@/components/sources/SourcesGrid/SourcesGrid";
import { ChatTurn } from "@/types";

type BotMessageProps = Pick<
  ChatTurn,
  "answer" | "error" | "isPending" | "sources"
> & {
  onFileDownload: (fileName: string, bucketName: string) => void;
};

const BotMessage = ({
  answer,
  error,
  isPending,
  sources,
  onFileDownload,
}: BotMessageProps) => {
  const isWaitingForAnswer = isPending && (answer === "" || error !== null);
  const sanitizedAnswer = sanitizeString(answer);
  const showActions = !isPending && (sanitizedAnswer !== "" || error !== null);
  const showSources = showActions && Array.isArray(sources);

  const botResponse =
    error !== null ? (
      <div className="bot-message__error">
        <ErrorIcon />
        <p>{error}</p>
      </div>
    ) : (
      <div className="bot-message__text" data-testid="bot-message__text">
        <Markdown text={sanitizedAnswer} />
        {showActions && (
          <footer className="bot-message__footer">
            <CopyButton textToCopy={sanitizedAnswer} />
          </footer>
        )}
        {showSources && (
          <SourcesGrid sources={sources} onFileDownload={onFileDownload} />
        )}
      </div>
    );

  const className = classNames("bot-message", {
    "bot-message--waiting": isWaitingForAnswer,
    "bot-message--completed": !isWaitingForAnswer,
  });

  return (
    <div className={className} data-testid="bot-message">
      <ChatBotIcon className="bot-message__chat-bot-icon" />
      {isWaitingForAnswer ? <PulsingDot /> : botResponse}
    </div>
  );
};

export const MemoizedBotMessage = memo(BotMessage);
