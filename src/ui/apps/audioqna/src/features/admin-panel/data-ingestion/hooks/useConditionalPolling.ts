// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useRef } from "react";

import {
  END_DATA_STATUSES,
  POLLING_INTERVAL,
} from "@/features/admin-panel/data-ingestion/config/api";
import { selectIsAutorefreshEnabled } from "@/features/admin-panel/data-ingestion/store/dataIngestionSettings.slice";
import {
  FileDataItem,
  LinkDataItem,
} from "@/features/admin-panel/data-ingestion/types";
import { useAppSelector } from "@/store/hooks";

const isDataIngestionInProgress = (
  data: FileDataItem[] | LinkDataItem[] | undefined,
) => data?.some(({ status }) => !END_DATA_STATUSES.includes(status)) ?? false;

const useConditionalPolling = (
  data: FileDataItem[] | LinkDataItem[] | undefined,
  refetch: () => void,
) => {
  const isAutorefreshEnabled = useAppSelector(selectIsAutorefreshEnabled);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const clearPollingInterval = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  useEffect(() => {
    if (isAutorefreshEnabled && isDataIngestionInProgress(data)) {
      if (!intervalRef.current) {
        intervalRef.current = setInterval(() => {
          refetch();
        }, POLLING_INTERVAL);
      }
    } else {
      if (intervalRef.current) {
        clearPollingInterval();
      }
    }

    return () => {
      clearPollingInterval();
    };
  }, [data, refetch, isAutorefreshEnabled]);
};

export default useConditionalPolling;
