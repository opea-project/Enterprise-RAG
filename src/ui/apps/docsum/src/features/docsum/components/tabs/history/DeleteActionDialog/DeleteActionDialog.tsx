// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionDialog } from "@intel-enterprise-rag-ui/components";

import { removeHistoryItem } from "@/features/docsum/store/history.slice";
import { HistoryItemData } from "@/features/docsum/types/history";
import { useAppDispatch } from "@/store/hooks";

interface DeleteActionDialogProps {
  itemData: HistoryItemData;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const DeleteActionDialog = ({
  itemData: { id },
  isOpen,
  onOpenChange,
}: DeleteActionDialogProps) => {
  const dispatch = useAppDispatch();

  const handleDeleteConfirm = () => {
    dispatch(removeHistoryItem(id));
  };

  return (
    <ActionDialog
      title="Delete Summary"
      confirmLabel="Delete"
      confirmColor="error"
      isOpen={isOpen}
      onConfirm={handleDeleteConfirm}
      onOpenChange={onOpenChange}
    >
      <p className="text-xs">
        Are you sure you want to delete this summary?
        <br /> This action cannot be undone.
      </p>
    </ActionDialog>
  );
};

export default DeleteActionDialog;
