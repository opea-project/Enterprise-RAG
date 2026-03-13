// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsTitle } from "@/components/ScannerInputsTitle/ScannerInputsTitle";
import { ServiceArgumentCheckbox } from "@/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import { ServiceArgumentNumberInput } from "@/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import {
  MaliciousURLsScannerArgs,
  MaliciousURLsScannerConfig,
} from "@/configs/guards/scanners";
import {
  ScannerInputsProps,
  useGuardScannerInputs,
} from "@/hooks/useGuardScannerInputs";

export const MaliciousURLsScannerInputs = ({
  previousArgumentsValues,
  config,
  handlers,
}: ScannerInputsProps<
  MaliciousURLsScannerArgs,
  MaliciousURLsScannerConfig
>) => {
  const {
    titleCasedName,
    handleArgumentValueChange,
    handleArgumentValidityChange,
  } = useGuardScannerInputs("malicious_urls", handlers);

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
