// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./FilesInput.scss";

import classNames from "classnames";
import {
  ChangeEvent,
  Dispatch,
  DragEvent,
  SetStateAction,
  useRef,
  useState,
} from "react";
import { ImFolderUpload } from "react-icons/im";

import {
  INPUT_FILE_ACCEPT,
  sanitizeFiles,
  SUPPORTED_FILE_FORMATS_MSG,
  TOTAL_SIZE_LIMIT_MSG,
  validateFiles,
} from "@/utils/data-ingestion/files-input";

interface FilesInputProps {
  files: File[];
  setFiles: Dispatch<SetStateAction<File[]>>;
  disabled: boolean;
}

const FilesInput = ({ files, setFiles, disabled }: FilesInputProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const processNewFiles = async (newFiles: FileList) => {
    const fileArray = [...newFiles];
    const sanitizedFiles = sanitizeFiles(fileArray);
    const validationMessage = await validateFiles([
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
      <div
        className={classNames({
          "files-input-box": true,
          "files-input-box__disabled": disabled,
        })}
        onDragOver={handleFileInputDragOver}
        onDrop={handleFileInputDrop}
      >
        <ImFolderUpload fontSize={40} />
        <p>
          Drag and drop your files here or{" "}
          <button
            className="files-input-box__choose-file-btn"
            onClick={handleBrowseFilesButtonClick}
          >
            choose files
          </button>
        </p>
        <p className="text-xs">{TOTAL_SIZE_LIMIT_MSG}</p>
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
      {errorMessage !== "" && (
        <div className="files-input-error-alert">{errorMessage}</div>
      )}
      <p className="pt-2 text-xs">{SUPPORTED_FILE_FORMATS_MSG}</p>
    </>
  );
};

export default FilesInput;
