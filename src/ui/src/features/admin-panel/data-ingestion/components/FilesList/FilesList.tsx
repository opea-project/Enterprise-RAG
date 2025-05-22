// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./FilesList.scss";

import { Dispatch, SetStateAction } from "react";

import IconButton from "@/components/ui/IconButton/IconButton";
import ListHeader from "@/features/admin-panel/data-ingestion/components/ListHeader/ListHeader";
import { formatFileSize } from "@/features/admin-panel/data-ingestion/utils";

interface FilesListProps {
  files: File[];
  setFiles: Dispatch<SetStateAction<File[]>>;
}

const FilesList = ({ files, setFiles }: FilesListProps) => {
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
      <ListHeader onClearListBtnPress={clearList} />
      <ul>
        {files.map((file, index) => (
          <li key={`file-list-item-${index}`} className="file-list-item">
            <div className="file-list-item-text">
              <p className="file-list-item__file-name">{file.name}</p>
              <p className="file-list-item__file-size">
                {formatFileSize(file.size)}
              </p>
            </div>
            <IconButton
              icon="delete"
              color="error"
              aria-label="Delete file from the list"
              onPress={() => removeDocumentFromList(index)}
            />
          </li>
        ))}
      </ul>
    </>
  );
};

export default FilesList;
