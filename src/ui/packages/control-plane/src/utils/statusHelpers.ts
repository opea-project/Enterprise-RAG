// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/**
 * Determines service readiness. For StatefulSets, returns "Ready" if at least one replica is ready.
 * @param {string} statusValue - The status string from the backend.
 * @param {string} key - The annotation key identifying the resource type.
 * @returns {string} The determined status.
 */
export const determineServiceReadiness = (
  statusValue: string,
  key: string,
): string => {
  const isStatefulSet = key.startsWith("StatefulSet:apps/v1:");
  const baseStatus = statusValue.split(";")[0];

  if (isStatefulSet && baseStatus === "Not ready") {
    const readyMatch = statusValue.match(/(\d+)\s+ready/);
    if (readyMatch) {
      const readyReplicas = parseInt(readyMatch[1], 10);
      if (readyReplicas > 0) {
        return "Ready";
      }
    }
  }

  return baseStatus;
};

export interface ParseServiceDetailsConfig<T extends string> {
  /** Maps service names to graph node IDs */
  serviceNameNodeIdMap: Record<string, T>;
  /** Array of all possible service node IDs in the graph */
  serviceNodeIds: readonly T[];
  /** Optional array of service names to exclude from processing */
  excludedServices?: string[];
  /** Function to convert snake_case to Title Case for display labels */
  formatSnakeCaseToTitleCase: (text: string) => string;
  /** Function to format service detail values for display */
  formatServiceDetailValue: (value: string) => string;
}

export interface GetServicesDetailsResponse {
  spec: {
    nodes: {
      root: {
        steps: Array<{
          internalService: {
            serviceName: string;
            config?: Record<string, string>;
          };
        }>;
      };
    };
  };
  status: {
    annotations: Record<string, string>;
  };
}

export interface FetchedServiceDetails {
  [serviceNodeId: string]: {
    status?: string;
    details?: Record<string, string>;
  };
}

/**
 * Parses the GMConnector backend response into a structured format for the UI.
 * @param {GetServicesDetailsResponse} response - The GMConnector response from the backend.
 * @param {ParseServiceDetailsConfig<T>} config - Configuration with service mappings and formatters.
 * @returns {FetchedServiceDetails} Service details mapped by node ID.
 */
export const parseServiceDetailsResponseData = <T extends string>(
  response: GetServicesDetailsResponse,
  config: ParseServiceDetailsConfig<T>,
): FetchedServiceDetails => {
  const {
    serviceNameNodeIdMap,
    serviceNodeIds,
    excludedServices = ["router"],
    formatSnakeCaseToTitleCase,
    formatServiceDetailValue,
  } = config;

  const {
    spec: {
      nodes: {
        root: { steps },
      },
    },
    status: { annotations },
  } = response;

  let usedVectorDb = "";
  const statusEntries = Object.entries(annotations)
    .filter(
      ([key]) =>
        (key.startsWith("Deployment:apps/v1:") ||
          key.startsWith("StatefulSet:apps/v1:")) &&
        !excludedServices.some((excluded) => key.includes(excluded)),
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

      const status = determineServiceReadiness(value, key);

      return [serviceNodeId, status];
    })
    .filter(([serviceNodeId]) => serviceNodeId !== undefined);
  const statuses = Object.fromEntries(statusEntries);

  const metadataEntries = steps
    .map((step): [string, Record<string, string>] => {
      const serviceName = `v1:${step.internalService.serviceName}`;
      const serviceNodeId = serviceNameNodeIdMap[serviceName];

      const config = step.internalService.config ?? {};
      if (serviceNodeId === "vectordb" && usedVectorDb) {
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
  const metadata: Record<string, Record<string, string>> = Object.fromEntries(
    metadataEntries,
  );

  const serviceDetails: FetchedServiceDetails = Object.fromEntries(
    serviceNodeIds.map((id) => [id, {}]),
  );

  for (const serviceNodeId in serviceDetails) {
    const details = metadata[serviceNodeId];
    const status = statuses[serviceNodeId];
    serviceDetails[serviceNodeId] = { status, details };
  }
  return serviceDetails;
};
