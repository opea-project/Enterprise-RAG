// Copyright (C) 2024-2026 Intel Corporation
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

import type { OnDeleteChatHandler } from "@/components/chat-history/DeleteChatDialog/DeleteChatDialog";
import { DeleteChatDialog } from "@/components/chat-history/DeleteChatDialog/DeleteChatDialog";
import type { OnExportChatHandler } from "@/components/chat-history/ExportChatDialog/ExportChatDialog";
import { ExportChatDialog } from "@/components/chat-history/ExportChatDialog/ExportChatDialog";
import type { OnRenameChatHandler } from "@/components/chat-history/RenameChatDialog/RenameChatDialog";
import { RenameChatDialog } from "@/components/chat-history/RenameChatDialog/RenameChatDialog";
import { ChatHistoryItemData } from "@/types";

export type ChatItemAction = "rename" | "export" | "pin" | "delete" | AriaKey;
export type OnPinChangeHandler = () => void;

interface ChatHistoryItemMenuProps {
  itemData: ChatHistoryItemData;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  pinned: boolean;
  onPinChange: OnPinChangeHandler;
  onDelete: OnDeleteChatHandler;
  onExport: OnExportChatHandler;
  onRename: OnRenameChatHandler;
}

export const ChatHistoryItemMenu = ({
  itemData,
  isOpen,
  onOpenChange,
  pinned,
  onPinChange,
  onDelete,
  onExport,
  onRename,
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
        chatId={itemData.id}
        currentName={itemData.name}
        isOpen={selectedOption === "rename"}
        onOpenChange={() => setSelectedOption(null)}
        onRename={onRename}
      />
      <ExportChatDialog
        chatId={itemData.id}
        isOpen={selectedOption === "export"}
        onOpenChange={() => setSelectedOption(null)}
        onExport={onExport}
      />
      <DeleteChatDialog
        chatId={itemData.id}
        isOpen={selectedOption === "delete"}
        onOpenChange={() => setSelectedOption(null)}
        onDelete={onDelete}
      />
    </>
  );
};
