// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LLMInputGuardArgs } from "@/configs/guards/llmInputGuard";
import type { LLMOutputGuardArgs } from "@/configs/guards/llmOutputGuard";
import type { LLMArgs } from "@/configs/services/llm";
import type { PromptTemplateArgs } from "@/configs/services/promptTemplate";
import type { RerankerArgs } from "@/configs/services/reranker";
import type { RetrieverArgs } from "@/configs/services/retriever";
import type { ServiceStatus } from "@/types/index";

export interface FetchedServiceDetails {
  [serviceNodeId: string]: {
    status?: ServiceStatus;
    details?: { [key: string]: string };
  };
}

export interface FetchedServicesParameters {
  llmArgs?: LLMArgs;
  retrieverArgs?: RetrieverArgs;
  rerankerArgs?: RerankerArgs;
  promptTemplateArgs?: PromptTemplateArgs;
  inputGuardArgs?: LLMInputGuardArgs;
  outputGuardArgs?: LLMOutputGuardArgs;
}

export interface FetchedServicesData {
  details: FetchedServiceDetails;
  parameters?: FetchedServicesParameters;
}
