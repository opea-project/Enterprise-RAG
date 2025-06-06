// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

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
import { formatSnakeCaseToTitleCase } from "@/utils";

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
    streaming,
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
      streaming,
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
  const {
    spec: {
      nodes: {
        root: { steps },
      },
    },
    status: { annotations },
  } = response;

  // Map of service names from deployment/microservices-connector/config/samples to chatqa graph node IDs
  const serviceNameNodeIdMap: { [service: string]: string } = {
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

  let usedVectorDb = "";
  const statusEntries = Object.entries(annotations)
    .filter(
      ([key]) =>
        (key.startsWith("Deployment:apps/v1:") || key.startsWith("StatefulSet:apps/v1:")) &&
        !["fgp", "router"].includes(key), // Filter out fingerprint and router services
    )
    .map(([key, value]) => {
      // Extract the database name from the vector-db key
      const dbRegex = new RegExp(/(?<=:)[^:-]+(?=-)/);
      const dbNameMatch = key.match(dbRegex);
      if (key.includes("vector-db") && dbNameMatch) {
        usedVectorDb = dbNameMatch[0];
      }

      const serviceName =
        Object.keys(serviceNameNodeIdMap).find((serviceName) =>
          key.includes(serviceName),
        ) ?? "";
      const serviceNodeId = serviceNameNodeIdMap[serviceName];

      const status = value.split(";")[0];

      return [serviceNodeId, status];
    })
    .filter(([serviceNodeId]) => serviceNodeId !== undefined);
  const statuses = Object.fromEntries(statusEntries);

  const metadataEntries = steps
    .map((step): [string, { [key: string]: string }] => {
      const serviceName = `v1:${step.internalService.serviceName}`;
      const serviceNodeId = serviceNameNodeIdMap[serviceName];

      const config = step.internalService.config ?? {};
      if (serviceNodeId === "vectordb") {
        config.USED_VECTOR_DB = usedVectorDb;
      }

      const configEntries = Object.entries(config)
        .filter(
          ([key]) =>
            key !== "endpoint" &&
            !key.toLowerCase().includes("endpoint") &&
            !key.toLowerCase().includes("url"),
        )
        .map(([key, value]) => [
          formatSnakeCaseToTitleCase(key),
          formatServiceDetailValue(value),
        ]);

      const metadata = Object.fromEntries(configEntries);

      return [serviceNodeId, metadata];
    })
    .filter(([serviceNodeId]) => serviceNodeId !== undefined);
  const metadata: { [key: string]: { [key: string]: string } } =
    Object.fromEntries(metadataEntries);

  const serviceDetails: FetchedServiceDetails = {
    embedding_model_server: {},
    embedding: {},
    retriever: {},
    vectordb: {},
    reranker: {},
    reranker_model_server: {},
    prompt_template: {},
    input_guard: {},
    llm: {},
    vllm: {},
    output_guard: {},
  };

  for (const serviceNodeId in serviceDetails) {
    const details = metadata[serviceNodeId];
    const status = statuses[serviceNodeId];
    serviceDetails[serviceNodeId] = { status, details };
  }
  return serviceDetails;
};
