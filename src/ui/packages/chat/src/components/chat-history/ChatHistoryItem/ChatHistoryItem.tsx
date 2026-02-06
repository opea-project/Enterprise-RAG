// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatHistoryItem.scss";

import { Anchor, Button, Tooltip } from "@intel-enterprise-rag-ui/components";
import { PinFilledIcon } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import { useState } from "react";

import type { OnPinChangeHandler } from "@/components/chat-history/ChatHistoryItemMenu/ChatHistoryItemMenu";
import { ChatHistoryItemMenu } from "@/components/chat-history/ChatHistoryItemMenu/ChatHistoryItemMenu";
import type { OnDeleteChatHandler } from "@/components/chat-history/DeleteChatDialog/DeleteChatDialog";
import type { OnExportChatHandler } from "@/components/chat-history/ExportChatDialog/ExportChatDialog";
import type { OnRenameChatHandler } from "@/components/chat-history/RenameChatDialog/RenameChatDialog";
import { ChatHistoryItemData } from "@/types";

const TITLE_OVERFLOW_LIMIT = 12;
const PINNED_TITLE_OVERFLOW_LIMIT = 10;

export type OnChatHistoryItemPressHandler = (id: string) => void;

interface ChatHistoryItemProps {
  itemData: ChatHistoryItemData;
  pinned: boolean;
  onPinChange: OnPinChangeHandler;
  isActive: boolean;
  onPress: OnChatHistoryItemPressHandler;
  onDelete: OnDeleteChatHandler;
  onExport: OnExportChatHandler;
  onRename: OnRenameChatHandler;
}

export const ChatHistoryItem = ({
  itemData,
  pinned,
  onPinChange,
  isActive,
  onPress,
  onDelete,
  onExport,
  onRename,
}: ChatHistoryItemProps) => {
  const { name } = itemData;
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleItemPress = () => {
    if (isActive) return;
    onPress(itemData.id);
  };

  const className = classNames("chat-history-item", {
    "chat-history-item--active": isActive,
    "chat-history-item--has-menu-open": isMenuOpen,
    "chat-history-item--pinned": pinned,
    "chat-history-item--unpinned": !pinned,
  });

  let titleElement = <p className="chat-history-item__title">{name}</p>;
  const titleOverflowLimit = pinned
    ? PINNED_TITLE_OVERFLOW_LIMIT
    : TITLE_OVERFLOW_LIMIT;

  if (name.length > titleOverflowLimit) {
    titleElement = (
      <Tooltip
        title={name}
        trigger={<p className="chat-history-item__title">{name}</p>}
        placement="right"
      />
    );
  }

  return (
    <Anchor className={className} onPress={handleItemPress}>
      {pinned && (
        <Tooltip
          title="Unpin"
          trigger={
            <Button
              aria-label="Unpin chat"
              className="chat-history-item__pin-icon"
              onPress={onPinChange}
            >
              <PinFilledIcon />
            </Button>
          }
        />
      )}
      {titleElement}
      <ChatHistoryItemMenu
        itemData={itemData}
        isOpen={isMenuOpen}
        onOpenChange={setIsMenuOpen}
        pinned={pinned}
        onPinChange={onPinChange}
        onDelete={onDelete}
        onExport={onExport}
        onRename={onRename}
      />
    </Anchor>
  );
};
