// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ProcessingTimePopup.scss";

import { useEffect, useRef, useState } from "react";

import Popup from "@/components/ui/Popup/Popup";
import { END_DATA_STATUSES } from "@/features/admin-panel/data-ingestion/config/api";
import useProcessingTimeFormat from "@/features/admin-panel/data-ingestion/hooks/useProcessingTimeFormat";
import { DataStatus } from "@/features/admin-panel/data-ingestion/types";

type DurationKey =
  | "text_extractor_duration"
  | "text_compression_duration"
  | "text_splitter_duration"
  | "dpguard_duration"
  | "embedding_duration"
  | "ingestion_duration";

const durationLegendItems: {
  key: DurationKey;
  className: string;
  label: string;
}[] = [
  {
    key: "text_extractor_duration",
    className: "processing-time-popup--text-extractor",
    label: "Text Extractor",
  },
  {
    key: "text_compression_duration",
    className: "processing-time-popup--text-compression",
    label: "Text Compression",
  },
  {
    key: "text_splitter_duration",
    className: "processing-time-popup--text-splitter",
    label: "Text Splitter",
  },
  {
    key: "dpguard_duration",
    className: "processing-time-popup--dpguard",
    label: "Data Prep Guardrails",
  },
  {
    key: "embedding_duration",
    className: "processing-time-popup--embedding",
    label: "Embedding",
  },
  {
    key: "ingestion_duration",
    className: "processing-time-popup--ingestion",
    label: "Ingestion",
  },
];

interface ProcessingTimePopupProps {
  textExtractorDuration: number;
  textCompressionDuration: number;
  textSplitterDuration: number;
  dpguardDuration: number;
  embeddingDuration: number;
  ingestionDuration: number;
  processingDuration: number;
  jobStartTime: number;
  dataStatus: DataStatus;
}

const ProcessingTimePopup = ({
  textExtractorDuration = 0,
  textCompressionDuration = 0,
  textSplitterDuration = 0,
  dpguardDuration = 0,
  embeddingDuration = 0,
  ingestionDuration = 0,
  processingDuration = 0,
  jobStartTime = 0,
  dataStatus,
}: ProcessingTimePopupProps) => {
  const { formatProcessingTime } = useProcessingTimeFormat();
  const [timer, setTimer] = useState("");
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const startTime = jobStartTime * 1000;

    const updateTimer = () => {
      const currentTime = Date.now();
      const elapsedTime = Math.floor(currentTime - startTime);
      setTimer(formatProcessingTime(elapsedTime));
    };

    if (!END_DATA_STATUSES.includes(dataStatus)) {
      updateTimer();
      intervalRef.current = setInterval(updateTimer, 1000);
    } else {
      setTimer(formatProcessingTime(processingDuration));
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [dataStatus, formatProcessingTime, jobStartTime, processingDuration]);

  if (processingDuration <= 0) {
    return <span>{timer}</span>;
  }

  const popupTrigger = (
    <button
      className="processing-time-popup__trigger"
      role="button"
      tabIndex={0}
    >
      {timer}
    </button>
  );

  const formattedTotalProcessingTime = formatProcessingTime(processingDuration);

  const durations: Record<DurationKey, number> = {
    text_extractor_duration: textExtractorDuration,
    text_compression_duration: textCompressionDuration,
    text_splitter_duration: textSplitterDuration,
    dpguard_duration: dpguardDuration,
    embedding_duration: embeddingDuration,
    ingestion_duration: ingestionDuration,
  };

  return (
    <Popup popupTrigger={popupTrigger} placement="bottom">
      <div className="processing-time-popup">
        <header className="processing-time-popup__header">
          <p>Total Processing Time</p>
          <p className="processing-time-popup__time">
            {formattedTotalProcessingTime}
          </p>
        </header>
        <div className="processing-time-popup__bar">
          {durationLegendItems.map(({ key, className, label }) => {
            const percent =
              processingDuration > 0
                ? (durations[key] / processingDuration) * 100
                : 0;

            if (percent === 0) return null;

            return (
              <span
                key={key}
                className={className}
                style={{ width: `${percent}%`, height: "100%" }}
                title={label}
                aria-label={label}
              />
            );
          })}
        </div>
        {durationLegendItems.map(({ key, className, label }) => {
          const duration = durations[key];

          if (duration === 0) return null;

          return (
            <div key={key} className="processing-time-popup__legend-item">
              <span className={className}></span>
              <p>{label}</p>
              <p className="processing-time-popup__time">
                {formatProcessingTime(duration)}
              </p>
            </div>
          );
        })}
      </div>
    </Popup>
  );
};

export default ProcessingTimePopup;
