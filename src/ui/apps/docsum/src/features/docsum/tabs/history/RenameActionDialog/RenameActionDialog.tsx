// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  ActionDialog,
  addNotification,
  TextInput,
} from "@intel-enterprise-rag-ui/components";
import { ChangeEvent, useEffect, useRef, useState } from "react";

import { renameHistoryItem } from "@/features/docsum/tabs/history/store/history.slice";
import { useAppDispatch } from "@/store/hooks";
import { HistoryItemData } from "@/types";

const NAME_CHAR_LIMIT = 250;

interface RenameActionDialogProps {
  itemData: HistoryItemData;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const RenameActionDialog = ({
  itemData: { title, id },
  isOpen,
  onOpenChange,
}: RenameActionDialogProps) => {
  const textInputRef = useRef<HTMLInputElement>(null);
  const [newTitle, setNewTitle] = useState(title);

  useEffect(() => {
    if (isOpen) {
      setNewTitle(title.slice(0, NAME_CHAR_LIMIT));
      textInputRef.current?.focus();
    }
  }, [isOpen, title]);

  const dispatch = useAppDispatch();

  const handleTitleChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.value.length <= NAME_CHAR_LIMIT) {
      setNewTitle(event.target.value);
    } else {
      setNewTitle(event.target.value.slice(0, NAME_CHAR_LIMIT));
    }
  };

  const handleRenameConfirm = () => {
    if (newTitle.trim() && newTitle !== title) {
      dispatch(renameHistoryItem({ id, newName: newTitle.trim() }));
      dispatch(
        addNotification({
          severity: "success",
          text: "The summary has been renamed successfully.",
        }),
      );
    }

    setNewTitle(newTitle.trim());
  };

  const handleCloseDialog = () => {
    setNewTitle(title);
  };

  const isRenameActionDisabled = !newTitle.trim() || newTitle === title;

  return (
    <ActionDialog
      title="Rename Summary"
      isConfirmDisabled={isRenameActionDisabled}
      isOpen={isOpen}
      onConfirm={handleRenameConfirm}
      onCancel={handleCloseDialog}
      onOpenChange={onOpenChange}
    >
      <TextInput
        ref={textInputRef}
        value={newTitle}
        size="sm"
        label="Summary Title"
        name="new-name"
        onChange={handleTitleChange}
      />
      <p className="text-right text-xs">
        {newTitle.length} / {NAME_CHAR_LIMIT} characters
      </p>
    </ActionDialog>
  );
};

export default RenameActionDialog;
