// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { parseServiceDetailsResponseData as parseServiceDetailsShared } from "@intel-enterprise-rag-ui/control-plane";
import { formatSnakeCaseToTitleCase } from "@intel-enterprise-rag-ui/utils";

import { LLMInputGuardArgs } from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/llmInputGuard";
import { LLMOutputGuardArgs } from "@/features/admin-panel/control-plane/config/chat-qna-graph/guards/llmOutputGuard";
import { RetrieverSearchType } from "@/features/admin-panel/control-plane/config/chat-qna-graph/retriever";
import {
  AppendArgumentsParameters,
  FetchedServiceDetails,
  FetchedServicesParameters,
  GetServicesDetailsResponse,
} from "@/features/admin-panel/control-plane/types/api";
import { formatServiceDetailValue } from "@/features/admin-panel/control-plane/utils";

const SERVICE_NODE_IDS = [
  "embedding_model_server",
  "embedding",
  "retriever",
  "vectordb",
  "reranker",
  "reranker_model_server",
  "prompt_template",
  "input_guard",
  "llm",
  "vllm",
  "output_guard",
] as const;

const SERVICE_NAME_NODE_ID_MAP: Record<
  string,
  (typeof SERVICE_NODE_IDS)[number]
> = {
  "v1:tei-embedding-svc": "embedding_model_server",
  "v1:torchserve-embedding-svc": "embedding_model_server",
  "v1:embedding-svc": "embedding",
  "v1:retriever-svc": "retriever",
  "v1:redis-vector-db": "vectordb",
  "v1:reranking-svc": "reranker",
  "v1:tei-reranking-svc": "reranker_model_server",
  "v1:prompt-template-svc": "prompt_template",
  "v1:input-scan-svc": "input_guard",
  "v1:llm-svc": "llm",
  "v1:vllm-gaudi-svc": "vllm",
  "v1:vllm-service-m": "vllm",
  "v1:output-scan-svc": "output_guard",
};

export const parseServicesParameters = (
  parameters: AppendArgumentsParameters,
): FetchedServicesParameters => {
  const {
    max_new_tokens,
    top_k,
    top_p,
    typical_p,
    temperature,
    repetition_penalty,
    stream,
    search_type,
    k,
    user_prompt_template,
    system_prompt_template,
    distance_threshold,
    fetch_k,
    lambda_mult,
    rerank_score_threshold,
    score_threshold,
    top_n,
    input_guardrail_params,
    output_guardrail_params,
  } = parameters;

  return {
    llmArgs: {
      max_new_tokens,
      top_k,
      top_p,
      typical_p,
      temperature,
      repetition_penalty,
      stream,
    },
    retrieverArgs: {
      search_type: search_type as RetrieverSearchType,
      k,
      distance_threshold,
      fetch_k,
      lambda_mult,
      score_threshold,
    },
    rerankerArgs: { top_n, rerank_score_threshold },
    promptTemplateArgs: {
      user_prompt_template,
      system_prompt_template,
    },
    inputGuardArgs: input_guardrail_params as LLMInputGuardArgs,
    outputGuardArgs: output_guardrail_params as LLMOutputGuardArgs,
  };
};

export const parseServiceDetailsResponseData = (
  response: GetServicesDetailsResponse,
): FetchedServiceDetails => {
  return parseServiceDetailsShared(response, {
    serviceNameNodeIdMap: SERVICE_NAME_NODE_ID_MAP,
    serviceNodeIds: SERVICE_NODE_IDS,
    excludedServices: ["fgp", "router"],
    formatSnakeCaseToTitleCase,
    formatServiceDetailValue,
  }) as FetchedServiceDetails;
};
