// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChunksProgressBar.scss";

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
    <div className="chunks-progress-bar__wrapper">
      <progress
        className="chunks-progress-bar"
        value={processedChunks}
        max={totalChunks}
      ></progress>
      <p className="chunks-progress-bar__text">
        {processedChunks}&nbsp;/&nbsp;{totalChunks}&nbsp;({percentValue}%)
      </p>
    </div>
  );
};

export default ChunksProgressBar;
