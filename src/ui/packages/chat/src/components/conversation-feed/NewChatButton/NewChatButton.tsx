// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./NewChatButton.scss";

import { IconButton, Tooltip } from "@intel-enterprise-rag-ui/components";

interface NewChatButtonProps {
  onPress: () => void;
}

export const NewChatButton = ({ onPress }: NewChatButtonProps) => (
  <Tooltip
    title="Create new chat"
    trigger={
      <IconButton
        icon="new-chat"
        variant="contained"
        className="new-chat-btn"
        onPress={onPress}
      />
    }
    placement="bottom"
  />
);
