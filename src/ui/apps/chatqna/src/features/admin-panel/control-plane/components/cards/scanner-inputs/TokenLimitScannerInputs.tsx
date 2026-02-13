// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsProps } from "@/features/admin-panel/control-plane/components/cards/scanner-inputs";
import ScannerInputsTitle from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/ScannerInputsTitle";
import ServiceArgumentCheckbox from "@/features/admin-panel/control-plane/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentNumberInput from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import {
  TokenLimitScannerArgs,
  TokenLimitScannerConfig,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/scanners";
import useGuardScannerInputs from "@/features/admin-panel/control-plane/hooks/useGuardScannerInputs";

const TokenLimitScannerInputs = ({
  previousArgumentsValues,
  config,
  handlers,
}: ScannerInputsProps<TokenLimitScannerArgs, TokenLimitScannerConfig>) => {
  const {
    titleCasedName,
    handleArgumentValueChange,
    handleArgumentValidityChange,
  } = useGuardScannerInputs("token_limit", handlers);

  return (
    <>
      <ScannerInputsTitle>{titleCasedName}</ScannerInputsTitle>
      <ServiceArgumentCheckbox
        {...config.enabled}
        value={previousArgumentsValues.enabled}
        onArgumentValueChange={handleArgumentValueChange}
      />
      <ServiceArgumentNumberInput
        {...config.limit}
        value={previousArgumentsValues.limit}
        onArgumentValueChange={handleArgumentValueChange}
        onArgumentValidityChange={handleArgumentValidityChange}
      />
    </>
  );
};

export default TokenLimitScannerInputs;
