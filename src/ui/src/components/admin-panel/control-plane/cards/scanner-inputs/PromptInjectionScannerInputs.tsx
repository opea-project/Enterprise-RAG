// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsProps } from "@/components/admin-panel/control-plane/cards/scanner-inputs";
import ScannerInputsTitle from "@/components/admin-panel/control-plane/cards/scanner-inputs/ScannerInputsTitle";
import ServiceArgumentCheckbox from "@/components/admin-panel/control-plane/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentNumberInput from "@/components/admin-panel/control-plane/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import ServiceArgumentTextInput from "@/components/admin-panel/control-plane/ServiceArgumentTextInput/ServiceArgumentTextInput";
import {
  PromptInjectionScannerArgs,
  PromptInjectionScannerConfig,
} from "@/config/control-plane/guards/scanners";
import useGuardScannerInputs from "@/utils/hooks/useGuardScannerInputs";

const PromptInjectionScannerInputs = ({
  previousArgumentsValues,
  config,
  handlers,
}: ScannerInputsProps<
  PromptInjectionScannerArgs,
  PromptInjectionScannerConfig
>) => {
  const {
    titleCasedName,
    handleArgumentValueChange,
    handleArgumentValidityChange,
  } = useGuardScannerInputs("prompt_injection", handlers);

  return (
    <>
      <ScannerInputsTitle>{titleCasedName}</ScannerInputsTitle>
      <ServiceArgumentCheckbox
        {...config.enabled}
        initialValue={previousArgumentsValues.enabled}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentNumberInput
        {...config.threshold}
        initialValue={previousArgumentsValues.threshold}
        onArgumentValueChange={handleArgumentValueChange}
        onArgumentValidityChange={handleArgumentValidityChange}
      />
      <ServiceArgumentTextInput
        {...config.match_type}
        initialValue={previousArgumentsValues.match_type}
        onArgumentValueChange={handleArgumentValueChange}
        onArgumentValidityChange={handleArgumentValidityChange}
      />
    </>
  );
};

export default PromptInjectionScannerInputs;
