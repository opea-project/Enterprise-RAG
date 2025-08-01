// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef } from "react";

import Button, { ButtonColor } from "@/components/ui/Button/Button";
import Dialog, { DialogProps, DialogRef } from "@/components/ui/Dialog/Dialog";

interface ActionDialogProps
  extends Omit<DialogProps, "footer" | "isCentered" | "hasPlainHeader"> {
  confirmLabel?: string;
  cancelLabel?: string;
  confirmColor?: ButtonColor;
  isConfirmDisabled?: boolean;
  onConfirm: () => void;
  onCancel?: () => void;
}

const ActionDialog = ({
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
      isCentered
      hasPlainHeader
      onClose={handleClose}
      {...rest}
    >
      <div className="px-4 pb-4">
        {children}
        <div className="mt-4 flex justify-end gap-2">
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

export default ActionDialog;
