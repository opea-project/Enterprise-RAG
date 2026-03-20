// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useRef } from "react";

const POLLING_INTERVAL = 10000;

export const useControlPlanePolling = (
  refetch: () => void,
  isAutorefreshEnabled: boolean,
) => {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const clearPollingInterval = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  useEffect(() => {
    if (isAutorefreshEnabled) {
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
  }, [refetch, isAutorefreshEnabled]);
};
