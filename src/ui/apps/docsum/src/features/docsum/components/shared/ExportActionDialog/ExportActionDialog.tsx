// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  ActionDialog,
  addNotification,
  SelectInput,
} from "@intel-enterprise-rag-ui/components";
import { memo, useState } from "react";

import { ExportFormat } from "@/features/docsum/types/export";
import {
  EXPORT_FORMATS,
  exportSummary,
  generateExportFileName,
} from "@/features/docsum/utils/export";
import { useAppDispatch } from "@/store/hooks";

interface ExportActionDialogProps {
  summary: string;
  fileName: string;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  isDisabled?: boolean;
}

const ExportActionDialog = memo(
  ({
    summary,
    fileName,
    isOpen,
    onOpenChange,
    isDisabled = false,
  }: ExportActionDialogProps) => {
    const [selectedFormat, setSelectedFormat] = useState<ExportFormat>("txt");
    const dispatch = useAppDispatch();

    if (!summary || isDisabled) return null;

    const handleExportConfirm = async () => {
      if (!summary || !fileName) return;

      const exportFileName = generateExportFileName(fileName, selectedFormat);

      try {
        await exportSummary(summary, fileName, selectedFormat);

        dispatch(
          addNotification({
            severity: "success",
            text: `Summary exported successfully as ${exportFileName}`,
          }),
        );

        onOpenChange(false);
      } catch (error) {
        console.error("Error exporting summary:", error);

        dispatch(
          addNotification({
            severity: "error",
            text: "An error occurred while exporting the summary. Please try again.",
          }),
        );
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
        <div className="mb-4">
          <SelectInput
            label="Export Format"
            value={selectedFormat}
            items={EXPORT_FORMATS}
            size="sm"
            onChange={setSelectedFormat}
          />
        </div>
        <p className="text-white-600 text-xs">
          File will be saved as:{" "}
          <strong>{generateExportFileName(fileName, selectedFormat)}</strong>
        </p>
      </ActionDialog>
    );
  },
);

ExportActionDialog.displayName = "ExportActionDialog";

export default ExportActionDialog;
