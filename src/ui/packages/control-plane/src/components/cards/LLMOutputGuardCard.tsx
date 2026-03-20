// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { BanSubstringsScannerInputs } from "@/components/scanner-inputs/BanSubstringsScannerInputs";
import { BiasScannerInputs } from "@/components/scanner-inputs/BiasScannerInputs";
import { CodeScannerInputs } from "@/components/scanner-inputs/CodeScannerInputs";
import { MaliciousURLsScannerInputs } from "@/components/scanner-inputs/MaliciousURLsScannerInputs";
import { RelevanceScannerInputs } from "@/components/scanner-inputs/RelevanceScannerInputs";
import { ScannersArgumentsTitle } from "@/components/ScannersArgumentsTitle/ScannersArgumentsTitle";
import { SelectedServiceCard } from "@/components/SelectedServiceCard/SelectedServiceCard";
import {
  LLMOutputGuardArgs,
  llmOutputGuardFormConfig,
} from "@/configs/guards/llmOutputGuard";
import { useGuardServiceCard } from "@/hooks/useGuardServiceCard";
import { ControlPlaneCardProps } from "@/types/cards";

export const LLMOutputGuardCard = ({
  data: { id, status, displayName, outputGuardArgs, details },
  changeArguments,
}: ControlPlaneCardProps) => {
  const config = llmOutputGuardFormConfig;

  const { argumentsForm, handlers, footerProps } =
    useGuardServiceCard<LLMOutputGuardArgs>(id, outputGuardArgs, {
      changeArguments,
    });

  return (
    <SelectedServiceCard
      serviceStatus={status}
      serviceName={displayName}
      serviceDetails={details}
      footerProps={footerProps}
    >
      <ScannersArgumentsTitle>Scanners Arguments</ScannersArgumentsTitle>
      <BanSubstringsScannerInputs
        config={config.ban_substrings}
        previousArgumentsValues={argumentsForm.ban_substrings}
        handlers={handlers}
      />
      <CodeScannerInputs
        config={config.code}
        previousArgumentsValues={argumentsForm.code}
        handlers={handlers}
      />
      <BiasScannerInputs
        config={config.bias}
        previousArgumentsValues={argumentsForm.bias}
        handlers={handlers}
      />
      <RelevanceScannerInputs
        config={config.relevance}
        previousArgumentsValues={argumentsForm.relevance}
        handlers={handlers}
      />
      <MaliciousURLsScannerInputs
        config={config.malicious_urls}
        previousArgumentsValues={argumentsForm.malicious_urls}
        handlers={handlers}
      />
    </SelectedServiceCard>
  );
};
