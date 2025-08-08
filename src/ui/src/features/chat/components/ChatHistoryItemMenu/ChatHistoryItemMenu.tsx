// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatHistoryItemMenu.scss";

import { useState } from "react";
import { Key } from "react-aria-components";

import DeleteIcon from "@/components/icons/DeleteIcon/DeleteIcon";
import EditIcon from "@/components/icons/EditIcon/EditIcon";
import ExportIcon from "@/components/icons/ExportIcon/ExportIcon";
import IconButton from "@/components/ui/IconButton/IconButton";
import { Menu, MenuItem, MenuTrigger } from "@/components/ui/Menu/Menu";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import DeleteChatDialog from "@/features/chat/components/DeleteChatDialog/DeleteChatDialog";
import ExportChatDialog from "@/features/chat/components/ExportChatDialog/ExportChatDialog";
import RenameChatDialog from "@/features/chat/components/RenameChatDialog/RenameChatDialog";
import { ChatItemData } from "@/features/chat/types/api";

export type ChatItemAction = "rename" | "export" | "delete" | Key;

interface ChatHistoryItemMenuProps {
  itemData: ChatItemData;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const ChatHistoryItemMenu = ({
  itemData,
  isOpen,
  onOpenChange,
}: ChatHistoryItemMenuProps) => {
  const [selectedOption, setSelectedOption] = useState<ChatItemAction | null>(
    null,
  );

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
        onOpenChange={onOpenChange}
        ariaLabel="Chat History Item Menu"
      >
        <Menu onAction={setSelectedOption}>
          <MenuItem id="rename">
            <EditIcon />
            <span>Rename</span>
          </MenuItem>
          <MenuItem id="export">
            <ExportIcon />
            <span>Export</span>
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
