// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DocumentsList.scss";

import { Dispatch, SetStateAction } from "react";
import { BsTrash } from "react-icons/bs";

import ListHeader from "@/components/admin-panel/data-ingestion/ListHeader/ListHeader";

const formatFileSize = (fileSize: number) => {
  const units = ["B", "KB", "MB", "GB", "TB"];

  if (fileSize === 0) {
    return "0 B";
  }
  const n = 1024;
  const i = Math.floor(Math.log(fileSize) / Math.log(n));
  let size: number | string = parseFloat(String(fileSize / Math.pow(n, i)));
  if (+fileSize > n) {
    size = size.toFixed(1);
  }

  const unit = units[i];
  return `${size} ${unit}`;
};

interface DocumentsListProps {
  documents: File[];
  setDocuments: Dispatch<SetStateAction<File[]>>;
  disabled: boolean;
}

const DocumentsList = ({
  documents,
  setDocuments,
  disabled,
}: DocumentsListProps) => {
  const clearList = () => {
    setDocuments([]);
  };

  const removeDocumentFromList = (documentIndex: number) => {
    setDocuments((prevFiles) =>
      prevFiles.filter((_, index) => index !== documentIndex),
    );
  };

  return (
    <>
      <ListHeader disabled={disabled} onClearListBtnClick={clearList} />
      <ul>
        {documents.map((file, index) => (
          <li
            key={`document-list-item-${index}`}
            className="document-list-item"
          >
            <div className="document-list-item-text">
              <p className="document-list-item__file-name">{file.name}</p>
              <p className="document-list-item__file-size">
                {formatFileSize(file.size)}
              </p>
            </div>
            <button
              className="icon-button-outlined--danger"
              disabled={disabled}
              onClick={() => removeDocumentFromList(index)}
            >
              <BsTrash />
            </button>
          </li>
        ))}
      </ul>
    </>
  );
};

export default DocumentsList;
