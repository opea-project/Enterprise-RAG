// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Duration } from "luxon";

import {
  ProcessingTimeFormat,
  selectProcessingTimeFormat,
  setProcessingTimeFormat,
} from "@/features/admin-panel/data-ingestion/store/dataIngestionSettings.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const formatStandard = (ms: number) => {
  const duration = Duration.fromMillis(ms);
  return duration.toFormat("hh:mm:ss.SSS");
};

const formatCompact = (ms: number) => {
  const duration = Duration.fromMillis(ms).rescale().toObject();
  const parts = [];

  if (duration.hours && duration.hours > 0) parts.push(`${duration.hours}h`);
  if (duration.minutes && duration.minutes > 0)
    parts.push(`${duration.minutes}m`);
  if (duration.seconds && duration.seconds > 0)
    parts.push(`${duration.seconds}s`);
  if (duration.milliseconds && duration.milliseconds > 0)
    parts.push(`${duration.milliseconds}ms`);

  return parts.join(" ");
};

const useProcessingTimeFormat = () => {
  const processingTimeFormat = useAppSelector(selectProcessingTimeFormat);
  const dispatch = useAppDispatch();

  const formatFn =
    processingTimeFormat === "standard" ? formatStandard : formatCompact;

  const setFormat = (format: ProcessingTimeFormat) => {
    dispatch(setProcessingTimeFormat(format));
  };

  return {
    processingTimeFormat,
    formatProcessingTime: formatFn,
    setFormat,
  };
};

export default useProcessingTimeFormat;
