// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { formatSnakeCaseToTitleCase } from "@intel-enterprise-rag-ui/utils";

import {
  FetchedServiceDetails,
  GetServicesDetailsResponse,
} from "@/features/admin-panel/control-plane/types/api";
import { formatServiceDetailValue } from "@/features/admin-panel/control-plane/utils";

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

  const serviceNameNodeIdMap: { [service: string]: string } = {
    "v1:docsum-svc": "docsum",
    "v1:llm-svc": "llm",
    "v1:text-compression-svc": "text_compression",
    "v1:text-extractor-svc": "text_extractor",
    "v1:text-splitter-svc": "text_splitter",
    "v1:vllm-service-m": "vllm",
  };

  const statusEntries = Object.entries(annotations)
    .filter(
      ([key]) =>
        (key.startsWith("Deployment:apps/v1:") ||
          key.startsWith("StatefulSet:apps/v1:")) &&
        !["router"].includes(key), // Filter out router service
    )
    .map(([key, value]) => {
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
    docsum: {},
    llm: {},
    text_compression: {},
    text_extractor: {},
    text_splitter: {},
    vllm: {},
  };

  for (const serviceNodeId in serviceDetails) {
    const details = metadata[serviceNodeId];
    const status = statuses[serviceNodeId];
    serviceDetails[serviceNodeId] = { status, details };
  }
  return serviceDetails;
};
