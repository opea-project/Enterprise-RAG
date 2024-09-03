// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Dispatch, SetStateAction } from "react";

import DocumentsFileInput from "@/components/admin-panel/data-ingestion/DocumentsFileInput/DocumentsFileInput";
import DocumentsList from "@/components/admin-panel/data-ingestion/DocumentsList/DocumentsList";

interface DocumentsIngestionPanelProps {
  documents: File[];
  setDocuments: Dispatch<SetStateAction<File[]>>;
  disabled: boolean;
}

const DocumentsIngestionPanel = ({
  documents,
  setDocuments,
  disabled,
}: DocumentsIngestionPanelProps) => (
  <>
    <DocumentsFileInput setDocuments={setDocuments} disabled={disabled} />
    <DocumentsList
      documents={documents}
      setDocuments={setDocuments}
      disabled={disabled}
    />
  </>
);

export default DocumentsIngestionPanel;
