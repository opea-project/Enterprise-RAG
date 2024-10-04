// Copyright (C) 2024 Intel Corporation
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

const acceptedFileTypes =
  ".pdf,.html,.txt,.doc,.docx,.ppt,.pptx,.md,.xml,.json,.jsonl,.yaml,.xls,.xlsx,.csv";
const acceptedFileTypesArray = acceptedFileTypes.split(",");

const validateDocuments = (documents: File[] | FileList) => {
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
    if (!disabled) {
      const newFiles = [...event.dataTransfer.files];
      const validationMessage = validateDocuments(newFiles);
      setErrorMessage(validationMessage);
      if (validationMessage === "") {
        setDocuments((prevFiles) => [...prevFiles, ...newFiles]);
      }
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
      const validationMessage = validateDocuments(newFiles);
      setErrorMessage(validationMessage);
      if (validationMessage === "") {
        setDocuments((prevFiles) => [...prevFiles, ...newFiles]);
      }
    }
  };

  return (
    <>
      {errorMessage !== "" && (
        <p className="documents-file-input-error-alert">{errorMessage}</p>
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
        <p>
          Supported file formats:{" "}
          {acceptedFileTypes
            .split(",")
            .map((type) => type.replace(".", "").toUpperCase())
            .join(", ")}
        </p>
        <p>or</p>
        <button
          className="outlined-button--primary"
          disabled={disabled}
          onClick={handleBrowseFilesButtonClick}
        >
          Browse Files
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedFileTypes}
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
