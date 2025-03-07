// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/types/admin-panel/control-plane";

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
