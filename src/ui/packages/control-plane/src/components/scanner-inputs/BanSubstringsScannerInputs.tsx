// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsTitle } from "@/components/ScannerInputsTitle/ScannerInputsTitle";
import { ServiceArgumentCheckbox } from "@/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import { ServiceArgumentSelectInput } from "@/components/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import { ServiceArgumentTextInput } from "@/components/ServiceArgumentTextInput/ServiceArgumentTextInput";
import {
  BanSubstringsScannerArgs,
  BanSubstringsScannerConfig,
} from "@/configs/guards/scanners";
import {
  ScannerInputsProps,
  useGuardScannerInputs,
} from "@/hooks/useGuardScannerInputs";

export const BanSubstringsScannerInputs = ({
  previousArgumentsValues,
  config,
  handlers,
}: ScannerInputsProps<
  BanSubstringsScannerArgs,
  BanSubstringsScannerConfig
>) => {
  const {
    titleCasedName,
    handleArgumentValueChange,
    handleArgumentValidityChange,
  } = useGuardScannerInputs("ban_substrings", handlers);

  return (
    <>
      <ScannerInputsTitle>{titleCasedName}</ScannerInputsTitle>
      <ServiceArgumentCheckbox
        {...config.enabled}
        value={previousArgumentsValues.enabled}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentTextInput
        {...config.substrings}
        value={previousArgumentsValues.substrings}
        onArgumentValueChange={handleArgumentValueChange}
        onArgumentValidityChange={handleArgumentValidityChange}
      />
      <ServiceArgumentSelectInput
        {...config.match_type}
        value={previousArgumentsValues.match_type}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentCheckbox
        {...config.case_sensitive}
        value={previousArgumentsValues.case_sensitive}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentCheckbox
        {...config.redact}
        value={previousArgumentsValues.redact}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentCheckbox
        {...config.contains_all}
        value={previousArgumentsValues.contains_all}
        onArgumentValueChange={handleArgumentValueChange}
      />
    </>
  );
};
