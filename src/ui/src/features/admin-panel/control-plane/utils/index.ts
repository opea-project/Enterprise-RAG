// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LLMInputGuardArgs } from "@/features/admin-panel/control-plane/config/guards/llmInputGuard";
import { LLMOutputGuardArgs } from "@/features/admin-panel/control-plane/config/guards/llmOutputGuard";
import {
  RetrieverArgs,
  RetrieverSearchType,
  searchTypesArgsMap,
} from "@/features/admin-panel/control-plane/config/retriever";
import {
  FilterFormDataFunction,
  FilterInvalidArgumentsFunction,
} from "@/features/admin-panel/control-plane/hooks/useServiceCard";
import { ServiceDetailsResponse } from "@/features/admin-panel/control-plane/types/serviceDetailsResponse";
import {
  AppendArgumentsParameters,
  FetchedServiceDetails,
  ServicesParameters,
} from "@/features/admin-panel/control-plane/types/systemFingerprint";

export const parseServicesParameters = (
  parameters: AppendArgumentsParameters,
): ServicesParameters => {
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
    prompt_template,
    distance_threshold,
    fetch_k,
    lambda_mult,
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
    rerankerArgs: { top_n },
    promptTemplate: prompt_template,
    inputGuardArgs: input_guardrail_params as LLMInputGuardArgs,
    outputGuardArgs: output_guardrail_params as LLMOutputGuardArgs,
  };
};

export const parseServiceDetailsResponseData = (
  response: ServiceDetailsResponse,
): FetchedServiceDetails => {
  const {
    spec: {
      nodes: {
        root: { steps },
      },
    },
    status: { annotations },
  } = response;

  // Map of service names from deployment/components/gmc/microservices-connector/config/samples to chatqa graph node IDs
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
        key.startsWith("Deployment:apps/v1:") &&
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
      const serviceName = step.internalService.serviceName;
      const serviceNodeId = serviceNameNodeIdMap[serviceName];

      const config = step.internalService.config ?? {};
      const configEntries = Object.entries(config).filter(
        ([key]) =>
          key !== "endpoint" &&
          !key.toLowerCase().includes("endpoint") &&
          !key.toLowerCase().includes("url"),
      );

      const metadata = Object.fromEntries(configEntries);
      if (serviceNodeId === "vectordb") {
        metadata.USED_VECTOR_DB = usedVectorDb;
      }

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

export const filterRetrieverFormData: FilterFormDataFunction<RetrieverArgs> = (
  data,
) => {
  if (data?.search_type) {
    const visibleInputs = searchTypesArgsMap[data.search_type];
    const copyData: Partial<RetrieverArgs> = { search_type: data.search_type };
    for (const argumentName in data) {
      if (visibleInputs.includes(argumentName)) {
        copyData[argumentName] = data[argumentName];
      }
    }
    return copyData;
  } else {
    return data;
  }
};

export const filterInvalidRetrieverArguments: FilterInvalidArgumentsFunction<
  RetrieverArgs
> = (invalidArguments, data) => {
  if (data?.search_type) {
    const visibleInputs = searchTypesArgsMap[data.search_type];
    return invalidArguments.filter((arg) => visibleInputs.includes(arg));
  } else {
    return invalidArguments;
  }
};
