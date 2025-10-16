// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionDialog } from "@intel-enterprise-rag-ui/components";
import { downloadBlob } from "@intel-enterprise-rag-ui/utils";

import { HistoryItemData } from "@/types";

interface ExportActionDialogProps {
  itemData: HistoryItemData;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const ExportActionDialog = ({
  itemData: { summary, title },
  isOpen,
  onOpenChange,
}: ExportActionDialogProps) => {
  const handleExportConfirm = () => {
    if (summary) {
      const itemBlob = new Blob([summary], {
        type: "application/text",
      });
      downloadBlob(itemBlob, `${title}.txt`);
    }
  };

  return (
    <ActionDialog
      title="Export Summary"
      confirmLabel="Export"
      isOpen={isOpen}
      onConfirm={handleExportConfirm}
      onOpenChange={onOpenChange}
    >
      <p className="text-xs">
        Exported file will contain summary in a TXT format.
      </p>
    </ActionDialog>
  );
};

export default ExportActionDialog;
