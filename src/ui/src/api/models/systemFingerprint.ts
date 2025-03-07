// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LLMInputGuardArgs } from "@/config/control-plane/guards/llmInputGuard";
import { LLMOutputGuardArgs } from "@/config/control-plane/guards/llmOutputGuard";
import { LLMArgs } from "@/config/control-plane/llm";
import { RerankerArgs } from "@/config/control-plane/reranker";
import { RetrieverArgs } from "@/config/control-plane/retriever";
import {
  ServiceArgumentInputValue,
  ServiceStatus,
} from "@/types/admin-panel/control-plane";

export interface AppendArgumentsRequestBody {
  text: string;
}

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
  [serviceName: string]: {
    status?: ServiceStatus;
    details?: { [key: string]: string };
  };
}
