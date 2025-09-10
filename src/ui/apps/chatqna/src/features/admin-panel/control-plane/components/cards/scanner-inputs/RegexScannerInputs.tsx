// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsProps } from "@/features/admin-panel/control-plane/components/cards/scanner-inputs";
import ScannerInputsTitle from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/ScannerInputsTitle";
import ServiceArgumentCheckbox from "@/features/admin-panel/control-plane/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentSelectInput from "@/features/admin-panel/control-plane/components/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import ServiceArgumentTextInput from "@/features/admin-panel/control-plane/components/ServiceArgumentTextInput/ServiceArgumentTextInput";
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

export default RegexScannerInputs;
