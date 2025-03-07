// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsProps } from "@/components/admin-panel/control-plane/cards/scanner-inputs";
import ScannerInputsTitle from "@/components/admin-panel/control-plane/cards/scanner-inputs/ScannerInputsTitle";
import ServiceArgumentCheckbox from "@/components/admin-panel/control-plane/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentTextInput from "@/components/admin-panel/control-plane/ServiceArgumentTextInput/ServiceArgumentTextInput";
import ServiceArgumentThreeStateSwitch from "@/components/admin-panel/control-plane/ServiceArgumentThreeStateSwitch/ServiceArgumentThreeStateSwitch";
import {
  RegexScannerArgs,
  RegexScannerConfig,
} from "@/config/control-plane/guards/scanners";
import useGuardScannerInputs from "@/utils/hooks/useGuardScannerInputs";

const RegexScannerInputs = ({
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
        initialValue={previousArgumentsValues.enabled}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentTextInput
        {...config.patterns}
        initialValue={previousArgumentsValues.patterns}
        onArgumentValueChange={handleArgumentValueChange}
        onArgumentValidityChange={handleArgumentValidityChange}
      />
      <ServiceArgumentTextInput
        {...config.match_type}
        initialValue={previousArgumentsValues.match_type}
        onArgumentValueChange={handleArgumentValueChange}
        onArgumentValidityChange={handleArgumentValidityChange}
      />
      <ServiceArgumentThreeStateSwitch
        {...config.redact}
        initialValue={previousArgumentsValues.redact}
        onChange={handleArgumentValueChange}
      />
    </>
  );
};

export default RegexScannerInputs;
