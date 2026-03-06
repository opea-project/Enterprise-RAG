// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { formatSnakeCaseToTitleCase } from "@intel-enterprise-rag-ui/utils";

import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/types/index";

export interface ScannerInputsProps<TValues, TConfig> {
  previousArgumentsValues: TValues;
  config: TConfig;
  handlers: {
    onArgumentValueChange: (
      scannerName: string,
    ) => OnArgumentValueChangeHandler;
    onArgumentValidityChange: (
      scannerName: string,
    ) => OnArgumentValidityChangeHandler;
  };
}

export const useGuardScannerInputs = (
  scannerId: string,
  handlers: {
    onArgumentValueChange: (
      scannerName: string,
    ) => OnArgumentValueChangeHandler;
    onArgumentValidityChange: (
      scannerName: string,
    ) => OnArgumentValidityChangeHandler;
  },
) => {
  const handleArgumentValueChange = handlers.onArgumentValueChange(scannerId);
  const handleArgumentValidityChange =
    handlers.onArgumentValidityChange(scannerId);

  const titleCasedName = formatSnakeCaseToTitleCase(scannerId);

  return {
    titleCasedName,
    handleArgumentValueChange,
    handleArgumentValidityChange,
  };
};
