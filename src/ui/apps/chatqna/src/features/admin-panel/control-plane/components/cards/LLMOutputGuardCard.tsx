// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/features/admin-panel/control-plane/components/cards";
import BanSubstringsScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/BanSubstringsScannerInputs";
import BiasScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/BiasScannerInputs";
import CodeScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/CodeScannerInputs";
import MaliciousURLsScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/MaliciousURLsScannerInputs";
import RelevanceScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/RelevanceScannerInputs";
import SelectedServiceCard from "@/features/admin-panel/control-plane/components/SelectedServiceCard/SelectedServiceCard";
import {
  LLMOutputGuardArgs,
  llmOutputGuardFormConfig,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/llmOutputGuard";
import useGuardServiceCard from "@/features/admin-panel/control-plane/hooks/useGuardServiceCard";

const LLMOutputGuardCard = ({
  data: { id, status, displayName, outputGuardArgs, details },
}: ControlPlaneCardProps) => {
  const { argumentsForm, handlers, footerProps } =
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
        previousArgumentsValues={argumentsForm.ban_substrings}
        handlers={handlers}
      />
      <CodeScannerInputs
        config={llmOutputGuardFormConfig.code}
        previousArgumentsValues={argumentsForm.code}
        handlers={handlers}
      />
      <BiasScannerInputs
        config={llmOutputGuardFormConfig.bias}
        previousArgumentsValues={argumentsForm.bias}
        handlers={handlers}
      />
      <RelevanceScannerInputs
        config={llmOutputGuardFormConfig.relevance}
        previousArgumentsValues={argumentsForm.relevance}
        handlers={handlers}
      />
      <MaliciousURLsScannerInputs
        config={llmOutputGuardFormConfig.malicious_urls}
        previousArgumentsValues={argumentsForm.malicious_urls}
        handlers={handlers}
      />
    </SelectedServiceCard>
  );
};

export default LLMOutputGuardCard;
