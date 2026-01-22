// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UserMessage.scss";

import { CopyButton } from "@intel-enterprise-rag-ui/components";
import { Markdown } from "@intel-enterprise-rag-ui/markdown";
import { memo, useState } from "react";

import { ChatTurn } from "@/types";

type UserMessageProps = Pick<ChatTurn, "question">;

const UserMessage = ({ question }: UserMessageProps) => {
  const [showCopyBtn, setShowCopyBtn] = useState(false);

  const handleMouseEnter = () => {
    setShowCopyBtn(true);
  };

  const handleMouseLeave = () => {
    setShowCopyBtn(false);
  };

  return (
    <article
      className="user-message"
      data-testid="user-message"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="flex w-full flex-col">
        <div className="user-message__text" data-testid="user-message__text">
          <Markdown text={question} />
        </div>
        <div className="user-message__footer">
          <CopyButton textToCopy={question} show={showCopyBtn} />
        </div>
      </div>
    </article>
  );
};

export default memo(UserMessage);
