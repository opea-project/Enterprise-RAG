// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UserMessage.scss";

import { CopyButton } from "@intel-enterprise-rag-ui/components";
import { Markdown } from "@intel-enterprise-rag-ui/markdown";
import { memo, useState } from "react";

import { ChatTurn } from "@/types";

type UserMessageProps = Pick<ChatTurn, "question">;

const UserMessage = ({ question }: UserMessageProps) => {
  const [showActionButtons, setShowActionButtons] = useState(false);

  const handleMouseEnter = () => {
    setShowActionButtons(true);
  };

  const handleMouseLeave = () => {
    setShowActionButtons(false);
  };

  return (
    <article
      className="user-message"
      data-testid="user-message"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="user-message__content">
        <div className="user-message__text" data-testid="user-message__text">
          <Markdown text={question} />
        </div>
        <div className="user-message__footer">
          <CopyButton textToCopy={question} show={showActionButtons} />
        </div>
      </div>
    </article>
  );
};

export const MemoizedUserMessage = memo(UserMessage);
