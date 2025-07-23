// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./NewChatButton.scss";

import classNames from "classnames";
import { useLocation } from "react-router-dom";

import IconButton from "@/components/ui/IconButton/IconButton";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
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

  const className = classNames("new-chat-btn");

  if (!isVisible) {
    return null;
  }

  return (
    <Tooltip
      title="Create new chat"
      trigger={
        <IconButton
          icon="new-chat"
          variant="contained"
          className={className}
          onPress={onNewChat}
        />
      }
      placement="bottom"
    />
  );
};

export default NewChatButton;
