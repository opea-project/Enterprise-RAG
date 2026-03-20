// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { BanSubstringsScannerInputs } from "@/components/scanner-inputs/BanSubstringsScannerInputs";
import { BanTopicsScannerInputs } from "@/components/scanner-inputs/BanTopicsScannerInputs";
import { CodeScannerInputs } from "@/components/scanner-inputs/CodeScannerInputs";
import { InvisibleTextScannerInputs } from "@/components/scanner-inputs/InvisibleTextScannerInputs";
import { PromptInjectionScannerInputs } from "@/components/scanner-inputs/PromptInjectionScannerInputs";
import { RegexScannerInputs } from "@/components/scanner-inputs/RegexScannerInputs";
import { SecretsScannerInputs } from "@/components/scanner-inputs/SecretsScannerInputs";
import { SentimentScannerInputs } from "@/components/scanner-inputs/SentimentScannerInputs";
import { TokenLimitScannerInputs } from "@/components/scanner-inputs/TokenLimitScannerInputs";
import { ToxicityScannerInputs } from "@/components/scanner-inputs/ToxicityScannerInputs";
import { ScannersArgumentsTitle } from "@/components/ScannersArgumentsTitle/ScannersArgumentsTitle";
import { SelectedServiceCard } from "@/components/SelectedServiceCard/SelectedServiceCard";
import {
  LLMInputGuardArgs,
  llmInputGuardFormConfig,
} from "@/configs/guards/llmInputGuard";
import { useGuardServiceCard } from "@/hooks/useGuardServiceCard";
import { ControlPlaneCardProps } from "@/types/cards";

export const LLMInputGuardCard = ({
  data: { id, status, displayName, inputGuardArgs, details },
  changeArguments,
}: ControlPlaneCardProps) => {
  const config = llmInputGuardFormConfig;

  const { argumentsForm, handlers, footerProps } =
    useGuardServiceCard<LLMInputGuardArgs>(id, inputGuardArgs, {
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
      <PromptInjectionScannerInputs
        config={config.prompt_injection}
        previousArgumentsValues={argumentsForm.prompt_injection}
        handlers={handlers}
      />
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
      <InvisibleTextScannerInputs
        config={config.invisible_text}
        previousArgumentsValues={argumentsForm.invisible_text}
        handlers={handlers}
      />
      <RegexScannerInputs
        config={config.regex}
        previousArgumentsValues={argumentsForm.regex}
        handlers={handlers}
      />
      <BanTopicsScannerInputs
        config={config.ban_topics}
        previousArgumentsValues={argumentsForm.ban_topics}
        handlers={handlers}
      />
      <SecretsScannerInputs
        config={config.secrets}
        previousArgumentsValues={argumentsForm.secrets}
        handlers={handlers}
      />
      <SentimentScannerInputs
        config={config.sentiment}
        previousArgumentsValues={argumentsForm.sentiment}
        handlers={handlers}
      />
      <TokenLimitScannerInputs
        config={config.token_limit}
        previousArgumentsValues={argumentsForm.token_limit}
        handlers={handlers}
      />
      <ToxicityScannerInputs
        config={config.toxicity}
        previousArgumentsValues={argumentsForm.toxicity}
        handlers={handlers}
      />
    </SelectedServiceCard>
  );
};
