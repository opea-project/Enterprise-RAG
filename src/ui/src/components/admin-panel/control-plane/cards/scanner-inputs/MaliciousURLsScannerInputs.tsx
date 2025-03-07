// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsProps } from "@/components/admin-panel/control-plane/cards/scanner-inputs";
import ScannerInputsTitle from "@/components/admin-panel/control-plane/cards/scanner-inputs/ScannerInputsTitle";
import ServiceArgumentCheckbox from "@/components/admin-panel/control-plane/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentNumberInput from "@/components/admin-panel/control-plane/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import {
  MaliciousURLsScannerArgs,
  MaliciousURLsScannerConfig,
} from "@/config/control-plane/guards/scanners";
import useGuardScannerInputs from "@/utils/hooks/useGuardScannerInputs";

const MaliciousURLsScannerInputs = ({
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

export default MaliciousURLsScannerInputs;
