// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DocumentsFileInput.scss";

import { Alert, Button, Typography } from "@mui/material";
import {
  ChangeEvent,
  Dispatch,
  DragEvent,
  SetStateAction,
  useRef,
  useState,
} from "react";

const acceptedFileTypes =
  ".pdf,.html,.txt,.doc,.docx,.ppt,.pptx,.md,.xml,.json,.jsonl,.yaml,.xls,.xlsx,.csv";
const acceptedFileTypesArray = acceptedFileTypes.split(",");

const validateDocuments = (documents: File[]) => {
  const hasSupportedExtension = Array.from(documents).every((doc) =>
    acceptedFileTypesArray.some((type) => doc.name.endsWith(type)),
  );
  return documents.length > 0 && hasSupportedExtension
    ? ""
    : "Some of the files you are trying to upload are in an unsupported format. Please try again";
};

interface DocumentsFileInputProps {
  setDocuments: Dispatch<SetStateAction<File[]>>;
  disabled: boolean;
}

const DocumentsFileInput = ({
  setDocuments,
  disabled,
}: DocumentsFileInputProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const handleFileInputDrop = (event: DragEvent) => {
    event.preventDefault();
    const newFiles = [...event.dataTransfer.files];
    const validationMessage = validateDocuments(newFiles);
    setErrorMessage(validationMessage);
    if (validationMessage === "") {
      setDocuments((prevFiles) => [...prevFiles, ...newFiles]);
    }
  };

  const handleFileInputDragOver = (event: DragEvent) => {
    event.preventDefault();
  };

  const handleBrowseFilesButtonClick = () => {
    fileInputRef.current!.click();
  };

  const handleFileInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const newFiles = event.target.files;
    if (newFiles) {
      setDocuments((prevFiles) => [...prevFiles, ...newFiles]);
    }
  };

  return (
    <>
      {errorMessage !== "" && (
        <Alert severity="error" className="documents-file-input-error-alert">
          {errorMessage}
        </Alert>
      )}
      <div
        onDrop={handleFileInputDrop}
        onDragOver={handleFileInputDragOver}
        className={`documents-file-input-box ${disabled ? "disabled" : ""}`}
      >
        <Typography variant="body1" fontWeight={600}>
          Drag and Drop files here
        </Typography>
        <Typography variant="caption" textAlign="center">
          Supported file formats:{" "}
          {acceptedFileTypes
            .split(",")
            .map((type) => type.replace(".", "").toUpperCase())
            .join(", ")}
        </Typography>
        <Typography variant="body2">or</Typography>
        <Button
          variant="outlined"
          disabled={disabled}
          onClick={handleBrowseFilesButtonClick}
        >
          Browse Files
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedFileTypes}
          disabled={disabled}
          multiple
          onChange={handleFileInputChange}
          className="file-input"
        />
      </div>
    </>
  );
};

export default DocumentsFileInput;
