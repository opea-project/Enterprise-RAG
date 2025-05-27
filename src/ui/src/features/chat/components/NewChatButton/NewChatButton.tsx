// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./NewChatButton.scss";

import classNames from "classnames";
import { useLocation } from "react-router-dom";

import Button from "@/components/ui/Button/Button";
import { paths } from "@/config/paths";
import { selectConversationTurns } from "@/features/chat/store/conversationFeed.slice";
import { useAppSelector } from "@/store/hooks";

interface NewChatButtonProps {
  onNewChat: () => void;
}

const NewChatButton = ({ onNewChat }: NewChatButtonProps) => {
  const location = useLocation();
  const isChatPage = location.pathname === paths.chat;

  const conversationTurns = useAppSelector(selectConversationTurns);

  const isVisible = isChatPage && conversationTurns.length > 0;

  const className = classNames("new-chat-btn", {
    visible: isVisible,
    invisible: !isVisible,
  });

  return (
    <Button
      variant="outlined"
      icon="plus"
      size="sm"
      className={className}
      onClick={onNewChat}
    >
      New chat
    </Button>
  );
};

export default NewChatButton;
