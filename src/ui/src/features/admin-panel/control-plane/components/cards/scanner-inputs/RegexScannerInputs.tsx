// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsProps } from "@/features/admin-panel/control-plane/components/cards/scanner-inputs";
import ScannerInputsTitle from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/ScannerInputsTitle";
import ServiceArgumentCheckbox from "@/features/admin-panel/control-plane/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentTextInput from "@/features/admin-panel/control-plane/components/ServiceArgumentTextInput/ServiceArgumentTextInput";
import ServiceArgumentThreeStateSwitch from "@/features/admin-panel/control-plane/components/ServiceArgumentThreeStateSwitch/ServiceArgumentThreeStateSwitch";
import {
  RegexScannerArgs,
  RegexScannerConfig,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/scanners";
import useGuardScannerInputs from "@/features/admin-panel/control-plane/hooks/useGuardScannerInputs";

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
