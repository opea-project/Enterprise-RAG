// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./BatchDeleteDialog.scss";

import { Button, Dialog, DialogRef } from "@intel-enterprise-rag-ui/components";
import { useRef } from "react";

interface BatchDeleteDialogProps {
  /** Whether the dialog is open */
  isOpen: boolean;
  /** Type of items being deleted */
  itemType: "files" | "links";
  /** Names of items to be deleted */
  itemNames: string[];
  /** Callback when confirm is clicked */
  onConfirm: () => void;
  /** Callback when dialog is closed */
  onClose: () => void;
}

/**
 * Confirmation dialog for batch delete action.
 */
const BatchDeleteDialog = ({
  isOpen,
  itemType,
  itemNames,
  onConfirm,
  onClose,
}: BatchDeleteDialogProps) => {
  const dialogRef = useRef<DialogRef>(null);

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <Dialog
      ref={dialogRef}
      title="Confirm Delete"
      maxWidth={500}
      onClose={onClose}
      footer={
        <div className="batch-delete-dialog__actions">
          <Button size="sm" color="error" onPress={handleConfirm}>
            Confirm
          </Button>
          <Button size="sm" variant="outlined" onPress={onClose}>
            Cancel
          </Button>
        </div>
      }
      isOpen={isOpen}
      isCentered
      hasPlainHeader
    >
      <div className="batch-delete-dialog">
        <p className="batch-delete-dialog__question">
          Are you sure you want to delete the following {itemType}?
        </p>
        {itemNames.length > 0 && (
          <ul className="batch-delete-dialog__list">
            {itemNames.map((name, index) => (
              <li key={index} className="batch-delete-dialog__item">
                {name}
              </li>
            ))}
          </ul>
        )}
      </div>
    </Dialog>
  );
};

export default BatchDeleteDialog;
