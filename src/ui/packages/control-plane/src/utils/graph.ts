// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Node } from "@xyflow/react";

import { FetchedServicesData } from "@/types/api/services";
import { ServiceData, ServiceDetails, ServiceStatus } from "@/types/index";

export const updateNodes = (
  graphNodes: Node<ServiceData>[],
  fetchedServicesData: FetchedServicesData,
  llmNodePositionNoGuards?: { x: number; y: number },
  llmModelServerNodePositionNoGuards?: { x: number; y: number },
) => {
  const updatedNodes = graphNodes
    .map((node) => updateNodeDetails(node, fetchedServicesData))
    .filter((node) => node.data.status);

  const updatedNodesIds = updatedNodes.map(({ id }) => id);
  const llmNodeIndex = updatedNodes.findIndex(({ id }) => id === "llm");
  const llmModelServerNodeIndex = updatedNodes.findIndex(
    ({ id }) => id === "llm_model_server",
  );

  if (
    !updatedNodesIds.includes("input_guard") &&
    !updatedNodesIds.includes("output_guard") &&
    llmNodeIndex !== -1 &&
    llmNodePositionNoGuards
  ) {
    updatedNodes[llmNodeIndex].position = llmNodePositionNoGuards;
  }

  if (
    !updatedNodesIds.includes("input_guard") &&
    !updatedNodesIds.includes("output_guard") &&
    llmModelServerNodeIndex !== -1 &&
    llmModelServerNodePositionNoGuards
  ) {
    updatedNodes[llmModelServerNodeIndex].position =
      llmModelServerNodePositionNoGuards;
  }

  return updatedNodes;
};

export const updateNodeDetails = (
  node: Node<ServiceData>,
  fetchedServicesData: FetchedServicesData,
): Node<ServiceData> => {
  const nodeId = node.data.id;
  let nodeDetails: ServiceDetails = {};
  let nodeStatus: ServiceStatus | undefined;

  const { details: serviceDetails, parameters } = fetchedServicesData;
  let nodeDisplayName: string | undefined;
  if (serviceDetails[nodeId]) {
    const { details, status, displayName } = serviceDetails[nodeId];
    nodeDetails = details || {};
    nodeStatus = status as ServiceStatus;
    nodeDisplayName = displayName;
  }

  const servicesArgsMap: Record<string, unknown> = {
    llmArgs: parameters?.llmArgs,
    rerankerArgs: parameters?.rerankerArgs,
    retrieverArgs: parameters?.retrieverArgs,
    inputGuardArgs: parameters?.inputGuardArgs,
    outputGuardArgs: parameters?.outputGuardArgs,
    promptTemplateArgs: parameters?.promptTemplateArgs,
  };

  for (const [key, value] of Object.entries(servicesArgsMap)) {
    if (node.data[key] !== undefined && value !== undefined) {
      return {
        ...node,
        data: {
          ...node.data,
          details: nodeDetails,
          status: nodeStatus,
          ...(nodeDisplayName && { displayName: nodeDisplayName }),
          [key]: value,
        },
      };
    }
  }

  return {
    ...node,
    data: {
      ...node.data,
      details: nodeDetails,
      status: nodeStatus,
      ...(nodeDisplayName && { displayName: nodeDisplayName }),
    },
  };
};
