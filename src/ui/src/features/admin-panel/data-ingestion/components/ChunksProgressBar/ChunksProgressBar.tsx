// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ProgressBar from "@/components/ui/ProgressBar/ProgressBar";

interface ChunksProgressBarProps {
  processedChunks: number;
  totalChunks: number;
}

const ChunksProgressBar = ({
  processedChunks,
  totalChunks,
}: ChunksProgressBarProps) => {
  const percentValue =
    totalChunks > 0 ? Math.round((processedChunks / totalChunks) * 100) : 0;

  return (
    <div className="flex flex-nowrap items-center gap-2">
      <ProgressBar value={processedChunks} maxValue={totalChunks} />
      <p className="text-xs">
        {processedChunks}&nbsp;/&nbsp;{totalChunks}&nbsp;({percentValue}%)
      </p>
    </div>
  );
};

export default ChunksProgressBar;
