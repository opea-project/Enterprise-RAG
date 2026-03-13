// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsTitle } from "@/components/ScannerInputsTitle/ScannerInputsTitle";
import { ServiceArgumentCheckbox } from "@/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import {
  InvisibleTextScannerArgs,
  InvisibleTextScannerConfig,
} from "@/configs/guards/scanners";
import {
  ScannerInputsProps,
  useGuardScannerInputs,
} from "@/hooks/useGuardScannerInputs";

export const InvisibleTextScannerInputs = ({
  previousArgumentsValues,
  config,
  handlers,
}: ScannerInputsProps<
  InvisibleTextScannerArgs,
  InvisibleTextScannerConfig
>) => {
  const { titleCasedName, handleArgumentValueChange } = useGuardScannerInputs(
    "invisible_text",
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
    </>
  );
};
