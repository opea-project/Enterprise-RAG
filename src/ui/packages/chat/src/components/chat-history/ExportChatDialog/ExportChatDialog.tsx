// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ExportChatDialog.scss";

import { ActionDialog } from "@intel-enterprise-rag-ui/components";

export type OnExportChatHandler = (chatId: string) => void;

interface ExportChatDialogProps {
  chatId: string;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  onExport: OnExportChatHandler;
}

export const ExportChatDialog = ({
  chatId,
  isOpen,
  onOpenChange,
  onExport,
}: ExportChatDialogProps) => {
  const handleExportConfirm = () => {
    onExport(chatId);
  };

  return (
    <ActionDialog
      title="Export Chat"
      confirmLabel="Export"
      isOpen={isOpen}
      onConfirm={handleExportConfirm}
      onOpenChange={onOpenChange}
    >
      <p className="export-chat-dialog__description">
        Exported file will contain conversation in a JSON format.
      </p>
    </ActionDialog>
  );
};
