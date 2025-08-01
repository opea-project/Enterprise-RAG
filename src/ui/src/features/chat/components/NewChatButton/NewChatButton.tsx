// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./NewChatButton.scss";

import IconButton from "@/components/ui/IconButton/IconButton";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import useChat from "@/features/chat/hooks/useChat";

const NewChatButton = () => {
  const { onNewChat } = useChat();
  return (
    <Tooltip
      title="Create new chat"
      trigger={
        <IconButton
          icon="new-chat"
          variant="contained"
          className="new-chat-btn"
          onPress={onNewChat}
        />
      }
      placement="bottom"
    />
  );
};

export default NewChatButton;
