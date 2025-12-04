// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { parseServiceDetailsResponseData as parseServiceDetailsShared } from "@intel-enterprise-rag-ui/control-plane";
import { formatSnakeCaseToTitleCase } from "@intel-enterprise-rag-ui/utils";

import {
  FetchedServiceDetails,
  GetServicesDetailsResponse,
} from "@/features/admin-panel/control-plane/types/api";
import { formatServiceDetailValue } from "@/features/admin-panel/control-plane/utils";

const SERVICE_NODE_IDS = [
  "docsum",
  "llm",
  "text_compression",
  "text_extractor",
  "text_splitter",
  "vllm",
] as const;

const SERVICE_NAME_NODE_ID_MAP: Record<
  string,
  (typeof SERVICE_NODE_IDS)[number]
> = {
  "v1:docsum-svc": "docsum",
  "v1:llm-svc": "llm",
  "v1:text-compression-svc": "text_compression",
  "v1:text-extractor-svc": "text_extractor",
  "v1:text-splitter-svc": "text_splitter",
  "v1:vllm-service-m": "vllm",
};

export const parseServiceDetailsResponseData = (
  response: GetServicesDetailsResponse,
): FetchedServiceDetails => {
  return parseServiceDetailsShared(response, {
    serviceNameNodeIdMap: SERVICE_NAME_NODE_ID_MAP,
    serviceNodeIds: SERVICE_NODE_IDS,
    excludedServices: ["router"],
    formatSnakeCaseToTitleCase,
    formatServiceDetailValue,
  }) as FetchedServiceDetails;
};
