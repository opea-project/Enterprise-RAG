// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsProps } from "@/features/admin-panel/control-plane/components/cards/scanner-inputs";
import ScannerInputsTitle from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/ScannerInputsTitle";
import ServiceArgumentCheckbox from "@/features/admin-panel/control-plane/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentNumberInput from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import {
  RelevanceScannerArgs,
  RelevanceScannerConfig,
} from "@/features/admin-panel/control-plane/config/guards/scanners";
import useGuardScannerInputs from "@/features/admin-panel/control-plane/hooks/useGuardScannerInputs";

const RelevanceScannerInputs = ({
  previousArgumentsValues,
  config,
  handlers,
}: ScannerInputsProps<RelevanceScannerArgs, RelevanceScannerConfig>) => {
  const {
    titleCasedName,
    handleArgumentValueChange,
    handleArgumentValidityChange,
  } = useGuardScannerInputs("relevance", handlers);

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

export default RelevanceScannerInputs;
