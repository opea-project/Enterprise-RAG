// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  DocFileIcon,
  DocxFileIcon,
  MdFileIcon,
  PdfFileIcon,
  PlainTextIcon,
  TextFileIcon,
} from "@intel-enterprise-rag-ui/icons";

import { HistoryItemData } from "@/features/docsum/types/history";

export const getFileIcon = (fileName: string) => {
  const fileExtension = fileName.split(".").pop()?.toLowerCase();
  if (fileExtension === "pdf") {
    return <PdfFileIcon />;
  } else if (fileExtension === "docx") {
    return <DocxFileIcon />;
  } else if (fileExtension === "doc") {
    return <DocFileIcon />;
  } else if (fileExtension === "md") {
    return <MdFileIcon />;
  } else {
    return <TextFileIcon />;
  }
};

export const getItemIcon = (itemData: HistoryItemData) => {
  if (itemData.sourceType === "file") {
    return getFileIcon(itemData.title);
  } else if (itemData.sourceType === "plainText") {
    return <PlainTextIcon />;
  } else {
    return null;
  }
};
