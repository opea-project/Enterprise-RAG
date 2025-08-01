// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UserMessage.scss";

import { memo, useState } from "react";

import MarkdownRenderer from "@/components/markdown/MarkdownRenderer";
import CopyButton from "@/components/ui/CopyButton/CopyButton";
import { ChatTurn } from "@/types";

type UserMessageProps = Pick<ChatTurn, "question">;

const UserMessage = memo(({ question }: UserMessageProps) => {
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
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="flex w-full flex-col">
        <div className="user-message__text">
          <MarkdownRenderer content={question} />
        </div>
        <div className="user-message__footer">
          <CopyButton textToCopy={question} show={showCopyBtn} />
        </div>
      </div>
    </article>
  );
});

export default UserMessage;
