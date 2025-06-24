// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/features/admin-panel/control-plane/components/cards";
import BanSubstringsScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/BanSubstringsScannerInputs";
import CodeScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/CodeScannerInputs";
import InvisibleTextScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/InvisibleTextScannerInputs";
import PromptInjectionScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/PromptInjectionScannerInputs";
import RegexScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/RegexScannerInputs";
import SecretsScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/SecretsScannerInputs";
import SentimentScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/SentimentScannerInputs";
import TokenLimitScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/TokenLimitScannerInputs";
import ToxicityScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/ToxicityScannerInputs";
import SelectedServiceCard from "@/features/admin-panel/control-plane/components/SelectedServiceCard/SelectedServiceCard";
import {
  LLMInputGuardArgs,
  llmInputGuardFormConfig,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/llmInputGuard";
import useGuardServiceCard from "@/features/admin-panel/control-plane/hooks/useGuardServiceCard";

const LLMInputGuardCard = ({
  data: { id, status, displayName, inputGuardArgs, details },
}: ControlPlaneCardProps) => {
  const { previousArgumentsValues, handlers, footerProps } =
    useGuardServiceCard<LLMInputGuardArgs>(id, inputGuardArgs);

  return (
    <SelectedServiceCard
      serviceStatus={status}
      serviceName={displayName}
      serviceDetails={details}
      footerProps={footerProps}
    >
      <p className="mb-1 mt-1 text-sm font-medium">Scanners Arguments</p>
      <PromptInjectionScannerInputs
        config={llmInputGuardFormConfig.prompt_injection}
        previousArgumentsValues={previousArgumentsValues.prompt_injection}
        handlers={handlers}
      />
      <BanSubstringsScannerInputs
        config={llmInputGuardFormConfig.ban_substrings}
        previousArgumentsValues={previousArgumentsValues.ban_substrings}
        handlers={handlers}
      />
      <CodeScannerInputs
        config={llmInputGuardFormConfig.code}
        previousArgumentsValues={previousArgumentsValues.code}
        handlers={handlers}
      />
      <InvisibleTextScannerInputs
        config={llmInputGuardFormConfig.invisible_text}
        previousArgumentsValues={previousArgumentsValues.invisible_text}
        handlers={handlers}
      />
      <RegexScannerInputs
        config={llmInputGuardFormConfig.regex}
        previousArgumentsValues={previousArgumentsValues.regex}
        handlers={handlers}
      />
      <SecretsScannerInputs
        config={llmInputGuardFormConfig.secrets}
        previousArgumentsValues={previousArgumentsValues.secrets}
        handlers={handlers}
      />
      <SentimentScannerInputs
        config={llmInputGuardFormConfig.sentiment}
        previousArgumentsValues={previousArgumentsValues.sentiment}
        handlers={handlers}
      />
      <TokenLimitScannerInputs
        config={llmInputGuardFormConfig.token_limit}
        previousArgumentsValues={previousArgumentsValues.token_limit}
        handlers={handlers}
      />
      <ToxicityScannerInputs
        config={llmInputGuardFormConfig.toxicity}
        previousArgumentsValues={previousArgumentsValues.toxicity}
        handlers={handlers}
      />
    </SelectedServiceCard>
  );
};

export default LLMInputGuardCard;
