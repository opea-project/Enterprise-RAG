// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsProps } from "@/components/admin-panel/control-plane/cards/scanner-inputs";
import ScannerInputsTitle from "@/components/admin-panel/control-plane/cards/scanner-inputs/ScannerInputsTitle";
import ServiceArgumentCheckbox from "@/components/admin-panel/control-plane/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentNumberInput from "@/components/admin-panel/control-plane/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import {
  CodeScannerArgs,
  CodeScannerConfig,
} from "@/config/control-plane/guards/scanners";
import useGuardScannerInputs from "@/utils/hooks/useGuardScannerInputs";

const CodeScannerInputs = ({
  previousArgumentsValues,
  config,
  handlers,
}: ScannerInputsProps<CodeScannerArgs, CodeScannerConfig>) => {
  const {
    titleCasedName,
    handleArgumentValueChange,
    handleArgumentValidityChange,
  } = useGuardScannerInputs("code", handlers);

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
    </>
  );
};

export default CodeScannerInputs;
