// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { downloadBlob } from "@intel-enterprise-rag-ui/utils";

import { ExportFormat } from "@/types/export";
import { createDocxFromSummary } from "@/utils/docx";

export const generateExportFileName = (
  fileName: string,
  format: ExportFormat,
): string => {
  const trimmedFileName = fileName.trim();

  const lastDotIndex = trimmedFileName.lastIndexOf(".");
  const fileNameWithoutExtension =
    lastDotIndex > 0
      ? trimmedFileName.substring(0, lastDotIndex)
      : trimmedFileName;

  const baseFileName = fileNameWithoutExtension.endsWith("_summary")
    ? fileNameWithoutExtension
    : `${fileNameWithoutExtension}_summary`;
  return `${baseFileName}.${format}`;
};

export const exportSummary = async (
  summary: string,
  fileName: string,
  format: ExportFormat,
): Promise<void> => {
  const exportFileName = generateExportFileName(fileName, format);

  let blob: Blob;
  if (format === "txt") {
    blob = new Blob([summary], { type: "text/plain" });
  } else if (format === "docx") {
    blob = await createDocxFromSummary(summary);
  } else {
    throw new Error(`Unsupported export format: ${format}`);
  }

  downloadBlob(blob, exportFileName);
};

export const EXPORT_FORMATS: ExportFormat[] = ["txt", "docx"];
