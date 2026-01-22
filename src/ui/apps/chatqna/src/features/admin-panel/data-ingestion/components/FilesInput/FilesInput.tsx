// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FileInput } from "@intel-enterprise-rag-ui/components";
import { getValidationErrorMessage } from "@intel-enterprise-rag-ui/input-validation";
import { sanitizeFiles } from "@intel-enterprise-rag-ui/utils";
import {
  ChangeEvent,
  Dispatch,
  DragEvent,
  SetStateAction,
  useRef,
  useState,
} from "react";

import { CLIENT_MAX_BODY_SIZE } from "@/config/api";
import { SUPPORTED_FILE_EXTENSIONS } from "@/features/admin-panel/data-ingestion/utils/constants";
import { validateFileInput } from "@/features/admin-panel/data-ingestion/validators/filesInput";

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
    try {
      await validateFileInput([...files, ...sanitizedFiles]);
      setErrorMessage("");
      setFiles((prevFiles) => [...prevFiles, ...sanitizedFiles]);
    } catch (error) {
      setErrorMessage(getValidationErrorMessage(error));
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
      totalSizeLimit={CLIENT_MAX_BODY_SIZE}
      supportedFileExtensions={SUPPORTED_FILE_EXTENSIONS}
      onDrop={handleFileInputDrop}
      onChange={handleFileInputChange}
      multiple
    />
  );
};

export default FilesInput;
