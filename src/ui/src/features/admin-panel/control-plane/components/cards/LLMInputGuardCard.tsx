// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/features/admin-panel/control-plane/components/cards";
import BanCompetitorsScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/BanCompetitorsScannerInputs";
import BanSubstringsScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/BanSubstringsScannerInputs";
import CodeScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/CodeScannerInputs";
import GibberishScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/GibberishScannerInputs";
import LanguageScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/LanguageScannerInputs";
import PromptInjectionScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/PromptInjectionScannerInputs";
import RegexScannerInputs from "@/features/admin-panel/control-plane/components/cards/scanner-inputs/RegexScannerInputs";
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
      <RegexScannerInputs
        config={llmInputGuardFormConfig.regex}
        previousArgumentsValues={previousArgumentsValues.regex}
        handlers={handlers}
      />
      <GibberishScannerInputs
        config={llmInputGuardFormConfig.gibberish}
        previousArgumentsValues={previousArgumentsValues.gibberish}
        handlers={handlers}
      />
      <LanguageScannerInputs
        config={llmInputGuardFormConfig.language}
        previousArgumentsValues={previousArgumentsValues.language}
        handlers={handlers}
      />
      <BanCompetitorsScannerInputs
        config={llmInputGuardFormConfig.ban_competitors}
        previousArgumentsValues={previousArgumentsValues.ban_competitors}
        handlers={handlers}
      />
    </SelectedServiceCard>
  );
};

export default LLMInputGuardCard;
