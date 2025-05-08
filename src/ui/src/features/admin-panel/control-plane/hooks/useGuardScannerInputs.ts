// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/features/admin-panel/control-plane/types";
import { formatSnakeCaseToTitleCase } from "@/utils";

const useGuardScannerInputs = (
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

export default useGuardScannerInputs;
