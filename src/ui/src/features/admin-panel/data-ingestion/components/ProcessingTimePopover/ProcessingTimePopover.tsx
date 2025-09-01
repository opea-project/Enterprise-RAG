// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ProcessingTimePopover.scss";

import { memo, useEffect, useRef, useState } from "react";

import Button from "@/components/ui/Button/Button";
import Popover from "@/components/ui/Popover/Popover";
import usePopover from "@/components/ui/Popover/usePopover";
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
    className: "processing-time-popover--text-extractor",
    label: "Text Extractor",
  },
  {
    key: "text_compression_duration",
    className: "processing-time-popover--text-compression",
    label: "Text Compression",
  },
  {
    key: "text_splitter_duration",
    className: "processing-time-popover--text-splitter",
    label: "Text Splitter",
  },
  {
    key: "dpguard_duration",
    className: "processing-time-popover--dpguard",
    label: "Data Prep Guardrails",
  },
  {
    key: "embedding_duration",
    className: "processing-time-popover--embedding",
    label: "Embedding",
  },
  {
    key: "ingestion_duration",
    className: "processing-time-popover--ingestion",
    label: "Ingestion",
  },
];

interface ProcessingTimePopoverProps {
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

const ProcessingTimePopover = memo(
  ({
    textExtractorDuration = 0,
    textCompressionDuration = 0,
    textSplitterDuration = 0,
    dpguardDuration = 0,
    embeddingDuration = 0,
    ingestionDuration = 0,
    processingDuration = 0,
    jobStartTime = 0,
    dataStatus,
  }: ProcessingTimePopoverProps) => {
    const { formatProcessingTime } = useProcessingTimeFormat();
    const [timer, setTimer] = useState("N/A");
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const { triggerRef, isOpen, togglePopover } =
      usePopover<HTMLButtonElement>();

    useEffect(() => {
      const updateTimer = () => {
        if (jobStartTime !== 0) {
          const startTime = jobStartTime * 1000;
          const currentTime = Date.now();
          const elapsedTime = Math.floor(currentTime - startTime);
          setTimer(formatProcessingTime(elapsedTime));
        }
      };

      if (!END_DATA_STATUSES.includes(dataStatus)) {
        updateTimer();
        intervalRef.current = setInterval(updateTimer, 1000);
      } else if (processingDuration !== 0) {
        setTimer(formatProcessingTime(processingDuration));
      } else {
        setTimer("N/A");
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

    const formattedTotalProcessingTime =
      formatProcessingTime(processingDuration);

    const durations: Record<DurationKey, number> = {
      text_extractor_duration: textExtractorDuration,
      text_compression_duration: textCompressionDuration,
      text_splitter_duration: textSplitterDuration,
      dpguard_duration: dpguardDuration,
      embedding_duration: embeddingDuration,
      ingestion_duration: ingestionDuration,
    };

    return (
      <>
        <Button
          ref={triggerRef}
          variant="text"
          className="processing-time-popover__trigger"
          onPress={togglePopover}
        >
          {timer}
        </Button>
        <Popover
          triggerRef={triggerRef}
          isOpen={isOpen}
          placement="bottom"
          ariaLabel="Processing Time Details"
          onOpenChange={togglePopover}
        >
          <div className="processing-time-popover">
            <header className="processing-time-popover__header">
              <p>Total Processing Time</p>
              <p className="processing-time-popover__time">
                {formattedTotalProcessingTime}
              </p>
            </header>
            <div className="processing-time-popover__bar">
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
                <div key={key} className="processing-time-popover__legend-item">
                  <span className={className}></span>
                  <p>{label}</p>
                  <p className="processing-time-popover__time">
                    {formatProcessingTime(duration)}
                  </p>
                </div>
              );
            })}
          </div>
        </Popover>
      </>
    );
  },
);

export default ProcessingTimePopover;
