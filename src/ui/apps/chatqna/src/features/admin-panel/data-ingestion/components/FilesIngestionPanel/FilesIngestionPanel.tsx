// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Dispatch, SetStateAction } from "react";

import FilesInput from "@/features/admin-panel/data-ingestion/components/FilesInput/FilesInput";
import FilesList from "@/features/admin-panel/data-ingestion/components/FilesList/FilesList";

interface FilesIngestionPanelProps {
  files: File[];
  setFiles: Dispatch<SetStateAction<File[]>>;
}

const FilesIngestionPanel = ({ files, setFiles }: FilesIngestionPanelProps) => (
  <section>
    <h2>Files</h2>
    <FilesInput files={files} setFiles={setFiles} />
    {files.length > 0 && <FilesList files={files} setFiles={setFiles} />}
  </section>
);

export default FilesIngestionPanel;
