// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./FilesInput.scss";

import {
  ChangeEvent,
  Dispatch,
  DragEvent,
  Fragment,
  SetStateAction,
  useRef,
  useState,
} from "react";

import FileIcon from "@/components/icons/FileIcon/FileIcon";
import Button from "@/components/ui/Button/Button";
import { sanitizeFiles } from "@/features/admin-panel/data-ingestion/utils";
import { supportedFileExtensions } from "@/features/admin-panel/data-ingestion/utils/constants";
import { validateFileInput } from "@/features/admin-panel/data-ingestion/validators/filesInput";
import { clientMaxBodySize } from "@/utils/validators/constants";

const fileInputAccept = supportedFileExtensions
  .map((extension) => `.${extension}`)
  .join(",");

const supportedFileFormatsMsg = `Supported file formats:  ${supportedFileExtensions
  .map((extension) => extension.toUpperCase())
  .join(", ")}`;

const totalSizeLimitMsg = `Single upload size limit: ${clientMaxBodySize}MB`;

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

  const handleFileInputDragOver = (event: DragEvent) => {
    event.preventDefault();
  };

  const handleBrowseFilesButtonPress = () => {
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
        className="files-input-box"
        onDragOver={handleFileInputDragOver}
        onDrop={handleFileInputDrop}
      >
        <FileIcon fontSize={20} />
        <p>Drag and Drop Files Here</p>
        <p className="text-xs">or</p>
        <Button size="sm" onPress={handleBrowseFilesButtonPress}>
          Browse Files
        </Button>
        <p className="text-xs">{totalSizeLimitMsg}</p>
        <input
          ref={fileInputRef}
          type="file"
          accept={fileInputAccept}
          multiple
          onChange={handleFileInputChange}
          className="hidden"
        />
      </div>
      {errorMessage !== "" && (
        <p className="files-input-error-alert">
          {errorMessage.split("\n").map((msg, index) => (
            <Fragment key={`files-input-error-msg-${index}`}>
              {msg}
              <br />
            </Fragment>
          ))}
        </p>
      )}
      <p className="pt-2 text-xs">{supportedFileFormatsMsg}</p>
    </>
  );
};

export default FilesInput;
