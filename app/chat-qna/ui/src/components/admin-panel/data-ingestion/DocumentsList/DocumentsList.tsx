// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DocumentsList.scss";

import DeleteIcon from "@mui/icons-material/Delete";
import { List, ListItem, Typography } from "@mui/material";
import { Dispatch, SetStateAction } from "react";

import ListHeader from "@/components/admin-panel/data-ingestion/ListHeader/ListHeader";
import SquareIconButton from "@/components/shared/SquareIconButton/SquareIconButton";

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

  const clearListBtnDisabled = documents.length === 0 || disabled;

  return (
    <>
      <ListHeader
        clearListBtnDisabled={clearListBtnDisabled}
        onClearListBtnClick={clearList}
      />
      <List>
        {documents.map((file, index) => (
          <ListItem
            key={`document-file-list-item-${index}`}
            className="file-list-item"
          >
            <div className="file-list-item-text">
              <Typography variant="body2">{file.name}</Typography>
              <Typography className="file-size-text">
                {formatFileSize(file.size)}
              </Typography>
            </div>
            <SquareIconButton
              color="error"
              disabled={disabled}
              onClick={() => removeDocumentFromList(index)}
            >
              <DeleteIcon fontSize="small" />
            </SquareIconButton>
          </ListItem>
        ))}
      </List>
    </>
  );
};

export default DocumentsList;
