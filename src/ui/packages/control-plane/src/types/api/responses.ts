// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { NamespaceStatus } from "@/types/api/namespaceStatus";
import type { FetchedServicesData } from "@/types/api/services";

export type GetServicesDataResponse = FetchedServicesData;

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
