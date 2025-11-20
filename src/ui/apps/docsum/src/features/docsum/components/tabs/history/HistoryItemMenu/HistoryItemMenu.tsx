// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./HistoryItemMenu.scss";

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
} from "@intel-enterprise-rag-ui/icons";
import { useState } from "react";
import { Key as AriaKey } from "react-aria-components";

import ExportActionDialog from "@/features/docsum/components/shared/ExportActionDialog/ExportActionDialog";
import DeleteActionDialog from "@/features/docsum/components/tabs/history/DeleteActionDialog/DeleteActionDialog";
import RenameActionDialog from "@/features/docsum/components/tabs/history/RenameActionDialog/RenameActionDialog";
import { HistoryItemData } from "@/features/docsum/types/history";

export type HistoryItemAction = "rename" | "export" | "delete" | AriaKey;

interface HistoryItemMenuProps {
  itemData: HistoryItemData;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const HistoryItemMenu = ({
  itemData,
  isOpen,
  onOpenChange,
}: HistoryItemMenuProps) => {
  const [selectedOption, setSelectedOption] =
    useState<HistoryItemAction | null>(null);

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
                aria-label="Manage Summary"
                className="history-item-menu__trigger"
              />
            }
          />
        }
        isOpen={isOpen}
        ariaLabel="Summary History Item Menu"
        onOpenChange={onOpenChange}
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
      <RenameActionDialog
        itemData={itemData}
        isOpen={selectedOption === "rename"}
        onOpenChange={() => setSelectedOption(null)}
      />
      {itemData.summary && (
        <ExportActionDialog
          summary={itemData.summary}
          fileName={itemData.title}
          isOpen={selectedOption === "export"}
          onOpenChange={() => setSelectedOption(null)}
        />
      )}
      <DeleteActionDialog
        itemData={itemData}
        isOpen={selectedOption === "delete"}
        onOpenChange={() => setSelectedOption(null)}
      />
    </>
  );
};

export default HistoryItemMenu;
