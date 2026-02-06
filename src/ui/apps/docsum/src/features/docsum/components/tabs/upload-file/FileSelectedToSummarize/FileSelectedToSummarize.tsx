// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./FileSelectedToSummarize.scss";

import { Button } from "@intel-enterprise-rag-ui/components";
import { useMemo } from "react";

import { getFileIcon } from "@/features/docsum/utils/render";

interface FileSelectedToSummarizeProps {
  fileName: string;
  isGeneratingSummary: boolean;
  onChangeFile: () => void;
  onDeleteFile: () => void;
}

const FileSelectedToSummarize = ({
  fileName,
  isGeneratingSummary,
  onChangeFile,
  onDeleteFile,
}: FileSelectedToSummarizeProps) => {
  const icon = useMemo(() => getFileIcon(fileName), [fileName]);

  return (
    <div className="file-selected-to-summarize">
      <span className="file-selected-to-summarize__icon">{icon}</span>
      <p className="file-selected-to-summarize__filename">{fileName}</p>
      <div className="file-selected-to-summarize__actions">
        <Button
          size="sm"
          variant="outlined"
          isDisabled={isGeneratingSummary}
          onClick={onChangeFile}
        >
          Change
        </Button>
        <Button
          color="error"
          size="sm"
          isDisabled={isGeneratingSummary}
          onClick={onDeleteFile}
        >
          Delete
        </Button>
      </div>
    </div>
  );
};

export default FileSelectedToSummarize;
