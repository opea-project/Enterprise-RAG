// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DocumentsFileInput.scss";

import classNames from "classnames";
import {
  ChangeEvent,
  Dispatch,
  DragEvent,
  SetStateAction,
  useRef,
  useState,
} from "react";

import {
  INPUT_FILE_ACCEPT,
  sanitizeFiles,
  SUPPORTED_FILE_FORMATS_MSG,
  TOTAL_SIZE_LIMIT_MSG,
  validateDocuments,
} from "@/utils/data-ingestion/documents-file-input";

interface DocumentsFileInputProps {
  documents: File[];
  setDocuments: Dispatch<SetStateAction<File[]>>;
  disabled: boolean;
}

const DocumentsFileInput = ({
  documents,
  setDocuments,
  disabled,
}: DocumentsFileInputProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const processNewFiles = async (newFiles: FileList) => {
    const fileArray = [...newFiles];
    const sanitizedFiles = sanitizeFiles(fileArray);
    const validationMessage = await validateDocuments([
      ...documents,
      ...sanitizedFiles,
    ]);
    setErrorMessage(validationMessage);
    if (validationMessage === "") {
      setDocuments((prevFiles) => [...prevFiles, ...sanitizedFiles]);
    }
  };

  const handleFileInputDrop = async (event: DragEvent) => {
    event.preventDefault();
    if (!disabled) {
      const newFiles = event.dataTransfer.files;
      await processNewFiles(newFiles);
    }
  };

  const handleFileInputDragOver = (event: DragEvent) => {
    event.preventDefault();
  };

  const handleBrowseFilesButtonClick = () => {
    fileInputRef.current!.click();
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
    <>
      {errorMessage !== "" && (
        <div className="documents-file-input-error-alert">{errorMessage}</div>
      )}
      <div
        onDrop={handleFileInputDrop}
        onDragOver={handleFileInputDragOver}
        className={classNames({
          "documents-file-input-box": true,
          "documents-file-input-box__disabled": disabled,
        })}
      >
        <p className="font-medium">Drag and Drop files here</p>
        <p>{SUPPORTED_FILE_FORMATS_MSG}</p>
        <p>or</p>
        <button
          className="outlined-button--primary"
          disabled={disabled}
          onClick={handleBrowseFilesButtonClick}
        >
          Browse Files
        </button>
        <p className="pt-2">{TOTAL_SIZE_LIMIT_MSG}</p>
        <input
          ref={fileInputRef}
          type="file"
          accept={INPUT_FILE_ACCEPT}
          disabled={disabled}
          multiple
          onChange={handleFileInputChange}
          className="hidden"
        />
      </div>
    </>
  );
};

export default DocumentsFileInput;
