// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UserMessage.scss";

import { memo } from "react";

import MarkdownRenderer from "@/components/markdown/MarkdownRenderer";
import { ConversationTurn } from "@/types";

type UserMessageProps = Pick<ConversationTurn, "question">;

const UserMessage = memo(({ question }: UserMessageProps) => (
  <article className="user-message">
    <div className="user-message__text">
      <MarkdownRenderer content={question} />
    </div>
  </article>
));

export default UserMessage;
