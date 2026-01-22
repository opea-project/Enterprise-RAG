// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatHistoryItemMenu.scss";

import {
  IconButton,
  Menu,
  MenuItem,
  MenuTrigger,
  Tooltip,
} from "@intel-enterprise-rag-ui/components";
import {
  DeleteIcon,
  EditIcon,
  ExportIcon,
  PinFilledIcon,
  PinIcon,
} from "@intel-enterprise-rag-ui/icons";
import { useState } from "react";
import { Key as AriaKey } from "react-aria-components";

import DeleteChatDialog from "@/features/chat/components/DeleteChatDialog/DeleteChatDialog";
import ExportChatDialog from "@/features/chat/components/ExportChatDialog/ExportChatDialog";
import RenameChatDialog from "@/features/chat/components/RenameChatDialog/RenameChatDialog";
import { ChatItemData } from "@/features/chat/types/api";

export type ChatItemAction = "rename" | "export" | "pin" | "delete" | AriaKey;

interface ChatHistoryItemMenuProps {
  itemData: ChatItemData;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  pinned: boolean;
  onPinChange: () => void;
}

const ChatHistoryItemMenu = ({
  itemData,
  isOpen,
  onOpenChange,
  pinned,
  onPinChange,
}: ChatHistoryItemMenuProps) => {
  const [selectedOption, setSelectedOption] = useState<ChatItemAction | null>(
    null,
  );

  const handleMenuAction = (key: ChatItemAction) => {
    if (key === "pin") {
      onPinChange();
    } else {
      setSelectedOption(key);
    }
  };

  return (
    <>
      <MenuTrigger
        trigger={
          <Tooltip
            title="More"
            trigger={
              <IconButton
                icon="more-options"
                size="sm"
                aria-label="Manage Chat"
                className="chat-history-item-menu__trigger"
              />
            }
          />
        }
        isOpen={isOpen}
        ariaLabel="Chat History Item Menu"
        onOpenChange={onOpenChange}
      >
        <Menu onAction={handleMenuAction}>
          <MenuItem id="rename">
            <EditIcon />
            <span>Rename</span>
          </MenuItem>
          <MenuItem id="export">
            <ExportIcon />
            <span>Export</span>
          </MenuItem>
          <MenuItem id="pin">
            {pinned ? <PinFilledIcon /> : <PinIcon />}
            <span>{pinned ? "Unpin" : "Pin"}</span>
          </MenuItem>
          <MenuItem id="delete">
            <DeleteIcon />
            <span>Delete</span>
          </MenuItem>
        </Menu>
      </MenuTrigger>
      <RenameChatDialog
        itemData={itemData}
        isOpen={selectedOption === "rename"}
        onOpenChange={() => setSelectedOption(null)}
      />
      <ExportChatDialog
        itemData={itemData}
        isOpen={selectedOption === "export"}
        onOpenChange={() => setSelectedOption(null)}
      />
      <DeleteChatDialog
        itemData={itemData}
        isOpen={selectedOption === "delete"}
        onOpenChange={() => setSelectedOption(null)}
      />
    </>
  );
};

export default ChatHistoryItemMenu;
