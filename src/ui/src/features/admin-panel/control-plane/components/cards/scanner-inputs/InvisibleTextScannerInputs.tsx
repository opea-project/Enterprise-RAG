// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScannerInputsProps } from "@/features/admin-panel/control-plane/components/cards/scanner-inputs";
import ScannerInputsTitle from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/ScannerInputsTitle";
import ServiceArgumentCheckbox from "@/features/admin-panel/control-plane/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import {
  InvisibleTextScannerArgs,
  InvisibleTextScannerConfig,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/scanners";
import useGuardScannerInputs from "@/features/admin-panel/control-plane/hooks/useGuardScannerInputs";

const InvisibleTextScannerInputs = ({
  previousArgumentsValues,
  config,
  handlers,
}: ScannerInputsProps<
  InvisibleTextScannerArgs,
  InvisibleTextScannerConfig
>) => {
  const { titleCasedName, handleArgumentValueChange } = useGuardScannerInputs(
    "invisible_text",
    handlers,
  );

  return (
    <>
      <ScannerInputsTitle>{titleCasedName}</ScannerInputsTitle>
      <ServiceArgumentCheckbox
        {...config.enabled}
        initialValue={previousArgumentsValues.enabled}
        onArgumentValueChange={handleArgumentValueChange}
      />
    </>
  );
};

export default InvisibleTextScannerInputs;
