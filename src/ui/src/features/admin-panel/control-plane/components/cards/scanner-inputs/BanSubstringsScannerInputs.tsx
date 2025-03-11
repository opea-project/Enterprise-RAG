// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsProps } from "@/features/admin-panel/control-plane/components/cards/scanner-inputs";
import ScannerInputsTitle from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/ScannerInputsTitle";
import ServiceArgumentCheckbox from "@/features/admin-panel/control-plane/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentTextInput from "@/features/admin-panel/control-plane/components/ServiceArgumentTextInput/ServiceArgumentTextInput";
import ServiceArgumentThreeStateSwitch from "@/features/admin-panel/control-plane/components/ServiceArgumentThreeStateSwitch/ServiceArgumentThreeStateSwitch";
import {
  BanSubstringsScannerArgs,
  BanSubstringsScannerConfig,
} from "@/features/admin-panel/control-plane/config/guards/scanners";
import useGuardScannerInputs from "@/features/admin-panel/control-plane/hooks/useGuardScannerInputs";

const BanSubstringsScannerInputs = ({
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
        initialValue={previousArgumentsValues.enabled}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentTextInput
        {...config.substrings}
        initialValue={previousArgumentsValues.substrings}
        onArgumentValueChange={handleArgumentValueChange}
        onArgumentValidityChange={handleArgumentValidityChange}
      />
      <ServiceArgumentTextInput
        {...config.match_type}
        initialValue={previousArgumentsValues.match_type}
        onArgumentValueChange={handleArgumentValueChange}
        onArgumentValidityChange={handleArgumentValidityChange}
      />
      <ServiceArgumentCheckbox
        {...config.case_sensitive}
        initialValue={previousArgumentsValues.case_sensitive}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentThreeStateSwitch
        {...config.redact}
        initialValue={previousArgumentsValues.redact}
        onChange={handleArgumentValueChange}
      />
      <ServiceArgumentThreeStateSwitch
        {...config.contains_all}
        initialValue={previousArgumentsValues.contains_all}
        onChange={handleArgumentValueChange}
      />
    </>
  );
};

export default BanSubstringsScannerInputs;
