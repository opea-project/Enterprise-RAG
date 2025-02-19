// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/types/admin-panel/control-plane";

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

  const titleCasedName = scannerId
    .split("_")
    .map((word) => `${word[0].toUpperCase()}${word.slice(1)}`)
    .join(" ");

  return {
    titleCasedName,
    handleArgumentValueChange,
    handleArgumentValidityChange,
  };
};

export default useGuardScannerInputs;
