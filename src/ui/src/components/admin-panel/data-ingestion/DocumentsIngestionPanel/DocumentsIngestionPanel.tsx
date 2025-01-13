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
  <section>
    <h2>Documents</h2>
    <DocumentsFileInput
      documents={documents}
      setDocuments={setDocuments}
      disabled={disabled}
    />
    {documents.length > 0 && (
      <DocumentsList
        documents={documents}
        setDocuments={setDocuments}
        disabled={disabled}
      />
    )}
  </section>
);

export default DocumentsIngestionPanel;
