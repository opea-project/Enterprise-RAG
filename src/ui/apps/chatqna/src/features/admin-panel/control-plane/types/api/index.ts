// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceStatus } from "@intel-enterprise-rag-ui/control-plane";

import { LLMInputGuardArgs } from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/llmInputGuard";
import { LLMOutputGuardArgs } from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/llmOutputGuard";
import { LLMArgs } from "@/features/admin-panel/control-plane/config/chat-qna-graph/llm";
import { PromptTemplateArgs } from "@/features/admin-panel/control-plane/config/chat-qna-graph/prompt-template";
import { RerankerArgs } from "@/features/admin-panel/control-plane/config/chat-qna-graph/reranker";
import { RetrieverArgs } from "@/features/admin-panel/control-plane/config/chat-qna-graph/retriever";
import { ServiceArgumentInputValue } from "@/features/admin-panel/control-plane/types";
import { NamespaceStatus } from "@/features/admin-panel/control-plane/types/api/namespaceStatus";

export type GetServicesDataResponse = FetchedServicesData;

export interface FetchedServicesData {
  details: FetchedServiceDetails;
  parameters: FetchedServicesParameters;
}

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

export type GetServicesDetailsResponse = NamespaceStatus;

export interface GetServicesParametersResponse {
  parameters: AppendArgumentsParameters;
}

export interface AppendArgumentsParameters {
  max_new_tokens: number;
  top_k: number;
  top_p: number;
  typical_p: number;
  temperature: number;
  repetition_penalty: number;
  stream: boolean;
  search_type: string;
  k: number;
  distance_threshold: number | null;
  fetch_k: number;
  lambda_mult: number;
  score_threshold: number;
  rerank_score_threshold: number | null;
  top_n: number;
  user_prompt_template: string;
  system_prompt_template: string;
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

export type ChangeArgumentsRequest = ServiceArgumentChange[];

interface ServiceArgumentChange {
  name: string;
  data: ChangeArgumentsRequestData;
}

export type ChangeArgumentsRequestData =
  | {
      [argumentName: string]: ServiceArgumentInputValue;
    }
  | LLMInputGuardArgs
  | LLMOutputGuardArgs;

export interface PostRetrieverQueryRequest extends RetrieverArgs, RerankerArgs {
  query: string;
  reranker: boolean;
  search_by?: string;
}
