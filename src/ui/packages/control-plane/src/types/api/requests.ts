// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LLMInputGuardArgs } from "@/configs/guards/llmInputGuard";
import type { LLMOutputGuardArgs } from "@/configs/guards/llmOutputGuard";
import type { RerankerArgs } from "@/configs/services/reranker";
import type { RetrieverArgs } from "@/configs/services/retriever";
import type { ServiceArgumentInputValue } from "@/types/index";

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
