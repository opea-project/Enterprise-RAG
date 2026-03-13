// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsTitle } from "@/components/ScannerInputsTitle/ScannerInputsTitle";
import { ServiceArgumentCheckbox } from "@/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import { ServiceArgumentSelectInput } from "@/components/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import { ServiceArgumentTextInput } from "@/components/ServiceArgumentTextInput/ServiceArgumentTextInput";
import {
  RegexScannerArgs,
  RegexScannerConfig,
} from "@/configs/guards/scanners";
import {
  ScannerInputsProps,
  useGuardScannerInputs,
} from "@/hooks/useGuardScannerInputs";

export const RegexScannerInputs = ({
  previousArgumentsValues,
  config,
  handlers,
}: ScannerInputsProps<RegexScannerArgs, RegexScannerConfig>) => {
  const {
    titleCasedName,
    handleArgumentValueChange,
    handleArgumentValidityChange,
  } = useGuardScannerInputs("regex", handlers);

  return (
    <>
      <ScannerInputsTitle>{titleCasedName}</ScannerInputsTitle>
      <ServiceArgumentCheckbox
        {...config.enabled}
        value={previousArgumentsValues.enabled}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentTextInput
        {...config.patterns}
        value={previousArgumentsValues.patterns}
        onArgumentValueChange={handleArgumentValueChange}
        onArgumentValidityChange={handleArgumentValidityChange}
      />
      <ServiceArgumentSelectInput
        {...config.match_type}
        value={previousArgumentsValues.match_type}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentCheckbox
        {...config.redact}
        value={previousArgumentsValues.redact}
        onArgumentValueChange={handleArgumentValueChange}
      />
    </>
  );
};
