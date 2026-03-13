// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsTitle } from "@/components/ScannerInputsTitle/ScannerInputsTitle";
import { ServiceArgumentCheckbox } from "@/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import { ServiceArgumentNumberInput } from "@/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import {
  SentimentScannerArgs,
  SentimentScannerConfig,
} from "@/configs/guards/scanners";
import {
  ScannerInputsProps,
  useGuardScannerInputs,
} from "@/hooks/useGuardScannerInputs";

export const SentimentScannerInputs = ({
  previousArgumentsValues,
  config,
  handlers,
}: ScannerInputsProps<SentimentScannerArgs, SentimentScannerConfig>) => {
  const {
    titleCasedName,
    handleArgumentValueChange,
    handleArgumentValidityChange,
  } = useGuardScannerInputs("sentiment", handlers);

  return (
    <>
      <ScannerInputsTitle>{titleCasedName}</ScannerInputsTitle>
      <ServiceArgumentCheckbox
        {...config.enabled}
        value={previousArgumentsValues.enabled}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentNumberInput
        {...config.threshold}
        value={previousArgumentsValues.threshold}
        onArgumentValueChange={handleArgumentValueChange}
        onArgumentValidityChange={handleArgumentValidityChange}
      />
    </>
  );
};
