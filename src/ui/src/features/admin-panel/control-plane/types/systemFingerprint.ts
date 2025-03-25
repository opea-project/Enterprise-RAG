// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LLMInputGuardArgs } from "@/features/admin-panel/control-plane/config/guards/llmInputGuard";
import { LLMOutputGuardArgs } from "@/features/admin-panel/control-plane/config/guards/llmOutputGuard";
import { LLMArgs } from "@/features/admin-panel/control-plane/config/llm";
import { RerankerArgs } from "@/features/admin-panel/control-plane/config/reranker";
import { RetrieverArgs } from "@/features/admin-panel/control-plane/config/retriever";
import {
  ServiceArgumentInputValue,
  ServiceStatus,
} from "@/features/admin-panel/control-plane/types";

export interface AppendArgumentsParameters {
  max_new_tokens: number;
  top_k: number;
  top_p: number;
  typical_p: number;
  temperature: number;
  repetition_penalty: number;
  streaming: boolean;
  search_type: string;
  k: number;
  distance_threshold: number | null;
  fetch_k: number;
  lambda_mult: number;
  score_threshold: number;
  top_n: number;
  prompt_template: string;
  input_guardrail_params: {
    [key: string]: {
      [key: string]: string | number | boolean | string[] | undefined | null;
    };
  };
  output_guardrail_params: {
    [key: string]: {
      [key: string]: string | number | boolean | string[] | undefined | null;
    };
  };
}

export interface ServicesParameters {
  llmArgs?: LLMArgs;
  retrieverArgs?: RetrieverArgs;
  rerankerArgs?: RerankerArgs;
  promptTemplate?: string;
  inputGuardArgs?: LLMInputGuardArgs;
  outputGuardArgs?: LLMOutputGuardArgs;
}

export type ChangeArgumentsRequestData =
  | {
      [argumentName: string]: ServiceArgumentInputValue;
    }
  | LLMInputGuardArgs
  | LLMOutputGuardArgs;

interface ServiceArgumentsToChange {
  name: string;
  data: ChangeArgumentsRequestData;
}

export type ChangeArgumentsRequestBody = ServiceArgumentsToChange[];

export interface FetchedServiceDetails {
  [serviceNodeId: string]: {
    status?: ServiceStatus;
    details?: { [key: string]: string };
  };
}
