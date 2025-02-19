// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/components/admin-panel/control-plane/cards";
import BanCompetitorsScannerInputs from "@/components/admin-panel/control-plane/cards/scanner-inputs/BanCompetitorsScannerInputs";
import BanSubstringsScannerInputs from "@/components/admin-panel/control-plane/cards/scanner-inputs/BanSubstringsScannerInputs";
import BiasScannerInputs from "@/components/admin-panel/control-plane/cards/scanner-inputs/BiasScannerInputs";
import CodeScannerInputs from "@/components/admin-panel/control-plane/cards/scanner-inputs/CodeScannerInputs";
import LanguageScannerInputs from "@/components/admin-panel/control-plane/cards/scanner-inputs/LanguageScannerInputs";
import MaliciousURLsScannerInputs from "@/components/admin-panel/control-plane/cards/scanner-inputs/MaliciousURLsScannerInputs";
import RelevanceScannerInputs from "@/components/admin-panel/control-plane/cards/scanner-inputs/RelevanceScannerInputs";
import SelectedServiceCard from "@/components/admin-panel/control-plane/SelectedServiceCard/SelectedServiceCard";
import {
  LLMOutputGuardArgs,
  llmOutputGuardFormConfig,
} from "@/config/control-plane/guards/llmOutputGuard";
import useGuardServiceCard from "@/utils/hooks/useGuardServiceCard";

const LLMOutputGuardCard = ({
  data: { id, status, displayName, outputGuardArgs, details },
}: ControlPlaneCardProps) => {
  const { previousArgumentsValues, handlers, footerProps } =
    useGuardServiceCard<LLMOutputGuardArgs>(id, outputGuardArgs);

  return (
    <SelectedServiceCard
      serviceStatus={status}
      serviceName={displayName}
      serviceDetails={details}
      footerProps={footerProps}
    >
      <p className="mb-1 mt-1 text-sm font-medium">Scanners Arguments</p>
      <BanSubstringsScannerInputs
        config={llmOutputGuardFormConfig.ban_substrings}
        previousArgumentsValues={previousArgumentsValues.ban_substrings}
        handlers={handlers}
      />
      <CodeScannerInputs
        config={llmOutputGuardFormConfig.code}
        previousArgumentsValues={previousArgumentsValues.code}
        handlers={handlers}
      />
      <BiasScannerInputs
        config={llmOutputGuardFormConfig.bias}
        previousArgumentsValues={previousArgumentsValues.bias}
        handlers={handlers}
      />
      <RelevanceScannerInputs
        config={llmOutputGuardFormConfig.relevance}
        previousArgumentsValues={previousArgumentsValues.relevance}
        handlers={handlers}
      />
      <BanCompetitorsScannerInputs
        config={llmOutputGuardFormConfig.ban_competitors}
        previousArgumentsValues={previousArgumentsValues.ban_competitors}
        handlers={handlers}
      />
      <LanguageScannerInputs
        config={llmOutputGuardFormConfig.language}
        previousArgumentsValues={previousArgumentsValues.language}
        handlers={handlers}
      />
      <MaliciousURLsScannerInputs
        config={llmOutputGuardFormConfig.malicious_urls}
        previousArgumentsValues={previousArgumentsValues.malicious_urls}
        handlers={handlers}
      />
    </SelectedServiceCard>
  );
};

export default LLMOutputGuardCard;
