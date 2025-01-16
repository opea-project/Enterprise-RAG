// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./FilesList.scss";

import { Dispatch, SetStateAction } from "react";
import { BsTrash } from "react-icons/bs";

import ListHeader from "@/components/admin-panel/data-ingestion/ListHeader/ListHeader";
import { formatFileSize } from "@/utils/data-ingestion";

interface FilesListProps {
  files: File[];
  setFiles: Dispatch<SetStateAction<File[]>>;
  disabled: boolean;
}

const FilesList = ({ files, setFiles, disabled }: FilesListProps) => {
  const clearList = () => {
    setFiles([]);
  };

  const removeDocumentFromList = (fileIndex: number) => {
    setFiles((prevFiles) =>
      prevFiles.filter((_, index) => index !== fileIndex),
    );
  };

  return (
    <>
      <ListHeader disabled={disabled} onClearListBtnClick={clearList} />
      <ul>
        {files.map((file, index) => (
          <li key={`file-list-item-${index}`} className="file-list-item">
            <div className="file-list-item-text">
              <p className="file-list-item__file-name">{file.name}</p>
              <p className="file-list-item__file-size">
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

export default FilesList;
