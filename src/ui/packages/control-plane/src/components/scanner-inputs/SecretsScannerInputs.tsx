// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsTitle } from "@/components/ScannerInputsTitle/ScannerInputsTitle";
import { ServiceArgumentCheckbox } from "@/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import { ServiceArgumentSelectInput } from "@/components/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import {
  SecretsScannerArgs,
  SecretsScannerConfig,
} from "@/configs/guards/scanners";
import {
  ScannerInputsProps,
  useGuardScannerInputs,
} from "@/hooks/useGuardScannerInputs";

export const SecretsScannerInputs = ({
  previousArgumentsValues,
  config,
  handlers,
}: ScannerInputsProps<SecretsScannerArgs, SecretsScannerConfig>) => {
  const { titleCasedName, handleArgumentValueChange } = useGuardScannerInputs(
    "secrets",
    handlers,
  );

  return (
    <>
      <ScannerInputsTitle>{titleCasedName}</ScannerInputsTitle>
      <ServiceArgumentCheckbox
        {...config.enabled}
        value={previousArgumentsValues.enabled}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentSelectInput
        {...config.redact_mode}
        value={previousArgumentsValues.redact_mode}
        onArgumentValueChange={handleArgumentValueChange}
      />
    </>
  );
};
