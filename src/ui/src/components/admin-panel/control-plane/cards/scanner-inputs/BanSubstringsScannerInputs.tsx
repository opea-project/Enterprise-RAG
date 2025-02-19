// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsProps } from "@/components/admin-panel/control-plane/cards/scanner-inputs";
import ScannerInputsTitle from "@/components/admin-panel/control-plane/cards/scanner-inputs/ScannerInputsTitle";
import ServiceArgumentCheckbox from "@/components/admin-panel/control-plane/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentTextInput from "@/components/admin-panel/control-plane/ServiceArgumentTextInput/ServiceArgumentTextInput";
import ServiceArgumentThreeStateSwitch from "@/components/admin-panel/control-plane/ServiceArgumentThreeStateSwitch/ServiceArgumentThreeStateSwitch";
import {
  BanSubstringsScannerArgs,
  BanSubstringsScannerConfig,
} from "@/config/control-plane/guards/scanners";
import useGuardScannerInputs from "@/utils/hooks/useGuardScannerInputs";

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
