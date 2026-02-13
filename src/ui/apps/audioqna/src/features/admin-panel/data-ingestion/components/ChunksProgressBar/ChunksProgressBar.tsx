// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ProgressBar } from "@intel-enterprise-rag-ui/components";
import { memo } from "react";

interface ChunksProgressBarProps {
  processedChunks: number;
  totalChunks: number;
}

const ChunksProgressBar = memo(
  ({ processedChunks, totalChunks }: ChunksProgressBarProps) => {
    const percentValue =
      totalChunks > 0 ? Math.round((processedChunks / totalChunks) * 100) : 0;

    return (
      <div className="flex flex-nowrap items-center gap-2">
        <ProgressBar
          value={processedChunks}
          maxValue={totalChunks}
          aria-label="Processed Chunks"
        />
        <p className="text-xs">
          {processedChunks}&nbsp;/&nbsp;{totalChunks}&nbsp;({percentValue}%)
        </p>
      </div>
    );
  },
);

ChunksProgressBar.displayName = "ChunksProgressBar";

export default ChunksProgressBar;
