// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { parseServiceDetailsResponseData as parseServiceDetailsShared } from "@intel-enterprise-rag-ui/control-plane";
import { formatSnakeCaseToTitleCase } from "@intel-enterprise-rag-ui/utils";

import {
  FetchedServiceDetails,
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
  "asr",
  "vllm-audio-cpu",
  "tts",
  "tts-model-server",
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
  "v1:asr-svc": "asr",
  "v1:tts-svc": "tts",
  "v1:tts-fastapi-model-server": "tts-model-server",
  "v1:vllm-audio-cpu": "vllm-audio-cpu",
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
