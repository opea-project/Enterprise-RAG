// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LLMInputGuardArgs } from "@/configs/guards/llmInputGuard";
import { LLMOutputGuardArgs } from "@/configs/guards/llmOutputGuard";
import { RetrieverSearchType } from "@/configs/services/retriever";
import { AppendArgumentsParameters } from "@/types/api/responses";
import { FetchedServicesParameters } from "@/types/api/services";

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
