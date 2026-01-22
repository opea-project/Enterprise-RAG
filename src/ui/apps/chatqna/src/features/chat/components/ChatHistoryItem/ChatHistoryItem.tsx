// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatHistoryItem.scss";

import { Anchor, Button, Tooltip } from "@intel-enterprise-rag-ui/components";
import { PinFilledIcon } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { paths } from "@/config/paths";
import ChatHistoryItemMenu from "@/features/chat/components/ChatHistoryItemMenu/ChatHistoryItemMenu";
import { ChatItemData } from "@/features/chat/types/api";

const TITLE_OVERFLOW_LIMIT = 12;
const PINNED_TITLE_OVERFLOW_LIMIT = 10;

interface ChatHistoryItemProps {
  itemData: ChatItemData;
  pinned: boolean;
  onPinChange: () => void;
}

const ChatHistoryItem = ({
  itemData,
  pinned,
  onPinChange,
}: ChatHistoryItemProps) => {
  const { id, name } = itemData;

  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = location.pathname === `${paths.chat}/${id}`;

  const handleEntryPress = () => {
    if (isActive) return;
    navigate(`${paths.chat}/${id}`);
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
    <Anchor className={className} onPress={handleEntryPress}>
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
      />
    </Anchor>
  );
};

export default ChatHistoryItem;
