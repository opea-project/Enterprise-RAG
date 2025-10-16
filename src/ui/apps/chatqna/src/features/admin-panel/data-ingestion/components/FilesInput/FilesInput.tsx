// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FileInput } from "@intel-enterprise-rag-ui/components";
import {
  ChangeEvent,
  Dispatch,
  DragEvent,
  SetStateAction,
  useRef,
  useState,
} from "react";

import { sanitizeFiles } from "@/features/admin-panel/data-ingestion/utils";
import { supportedFileExtensions } from "@/features/admin-panel/data-ingestion/utils/constants";
import { validateFileInput } from "@/features/admin-panel/data-ingestion/validators/filesInput";
import { clientMaxBodySize } from "@/utils/validators/constants";

interface FilesInputProps {
  files: File[];
  setFiles: Dispatch<SetStateAction<File[]>>;
}

const FilesInput = ({ files, setFiles }: FilesInputProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const processNewFiles = async (newFiles: FileList) => {
    const fileArray = [...newFiles];
    const sanitizedFiles = sanitizeFiles(fileArray);
    const validationMessage = await validateFileInput([
      ...files,
      ...sanitizedFiles,
    ]);
    setErrorMessage(validationMessage);
    if (validationMessage === "") {
      setFiles((prevFiles) => [...prevFiles, ...sanitizedFiles]);
    }

    // Clear file input value
    if (fileInputRef.current) {
      fileInputRef.current.files = null;
      fileInputRef.current.value = "";
    }
  };

  const handleFileInputDrop = async (event: DragEvent) => {
    event.preventDefault();

    const newFiles = event.dataTransfer.files;
    await processNewFiles(newFiles);
  };

  const handleFileInputChange = async (
    event: ChangeEvent<HTMLInputElement>,
  ) => {
    const newFiles = event.target.files;
    if (newFiles !== null && newFiles instanceof FileList) {
      await processNewFiles(newFiles);
    }
  };

  return (
    <FileInput
      errorMessage={errorMessage}
      totalSizeLimit={clientMaxBodySize}
      supportedFileExtensions={supportedFileExtensions}
      onDrop={handleFileInputDrop}
      onChange={handleFileInputChange}
      multiple
    />
  );
};

export default FilesInput;
