// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ActionDialog.scss";

import { useRef } from "react";

import { Button, ButtonColor } from "@/Button/Button";
import { Dialog, DialogProps, DialogRef } from "@/Dialog/Dialog";

interface ActionDialogProps
  extends Omit<DialogProps, "footer" | "isCentered" | "hasPlainHeader"> {
  /** Label for the confirm button */
  confirmLabel?: string;
  /** Label for the cancel button */
  cancelLabel?: string;
  /** Color of the confirm button */
  confirmColor?: ButtonColor;
  /** If true, disables the confirm button */
  isConfirmDisabled?: boolean;
  /** Callback for confirm action */
  onConfirm: () => void;
  /** Callback for cancel action */
  onCancel?: () => void;
}

/**
 * Action dialog component for confirmation dialogs with customizable labels, colors, and actions.
 */
export const ActionDialog = ({
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  confirmColor = "primary",
  isConfirmDisabled,
  onConfirm,
  onCancel,
  title,
  maxWidth = 400,
  children,
  ...rest
}: ActionDialogProps) => {
  const dialogRef = useRef<DialogRef>(null);

  const handleClose = () => {
    dialogRef.current?.close();
    onCancel?.();
  };

  const handleConfirm = () => {
    onConfirm();
    handleClose();
  };

  return (
    <Dialog
      ref={dialogRef}
      title={title}
      maxWidth={maxWidth}
      onClose={handleClose}
      isCentered
      hasPlainHeader
      {...rest}
    >
      <div className="action-dialog">
        {children}
        <div className="action-dialog__actions">
          <Button
            size="sm"
            color={confirmColor}
            isDisabled={isConfirmDisabled}
            onPress={handleConfirm}
          >
            {confirmLabel}
          </Button>
          <Button size="sm" variant="outlined" onPress={handleClose}>
            {cancelLabel}
          </Button>
        </div>
      </div>
    </Dialog>
  );
};
