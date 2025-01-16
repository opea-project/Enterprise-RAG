// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceDetailsResponse } from "@/api/models/serviceDetailsResponse";
import { FetchedServiceDetails } from "@/api/models/systemFingerprint";

const parseServiceDetailsResponseData = (
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

  const deploymentAnnotationsMap: { [key: string]: string } = {
    "Deployment:apps/v1:embedding-svc-deployment:chatqa": "embedding",
    "Deployment:apps/v1:input-scan-svc-deployment:chatqa": "input_guard",
    "Deployment:apps/v1:llm-svc-deployment:chatqa": "llm",
    "Deployment:apps/v1:vllm-service-m-deployment:chatqa": "vllm",
    "Deployment:apps/v1:output-scan-svc-deployment:chatqa": "output_guard",
    "Deployment:apps/v1:redis-vector-db-deployment:chatqa": "vectordb",
    "Deployment:apps/v1:reranking-svc-deployment:chatqa": "reranker",
    "Deployment:apps/v1:prompt-template-svc-deployment:chatqa":
      "prompt_template",
    "Deployment:apps/v1:retriever-svc-deployment:chatqa": "retriever",
    "Deployment:apps/v1:tei-reranking-svc-deployment:chatqa":
      "reranker_model_server",
    "Deployment:apps/v1:torchserve-embedding-svc-deployment:chatqa":
      "embedding_model_server",
  };

  const nodesStepsMap: { [key: string]: string } = {
    embedding: "embedding",
    torchserveembedding: "embedding_model_server",
    retriever: "retriever",
    vectordb: "vectordb",
    reranking: "reranker",
    teireranking: "reranker_model_server",
    prompttemplate: "prompt_template",
    llm: "llm",
    vllm: "vllm",
    tgi: "tgi",
  };

  let usedVectorDb = "";
  const statusEntries = Object.entries(annotations)
    .filter(
      ([key]) =>
        key.startsWith("Deployment:apps/v1:") && !key.includes("router"),
    )
    .map(([key, value]) => {
      let name = "";
      if (deploymentAnnotationsMap[key]) {
        name = deploymentAnnotationsMap[key];
        const dbRegex = new RegExp(/(?<=:)[^:-]+(?=-)/);
        const dbNameMatch = key.match(dbRegex);
        if (key.includes("vector-db") && dbNameMatch) {
          usedVectorDb = dbNameMatch[0];
        }
      }

      const status = value.split(";")[0];

      return [name, status];
    });
  const statuses = Object.fromEntries(statusEntries);

  const metadataEntries = steps.map((step) => {
    const stepName = step.name.toLowerCase();
    const name = nodesStepsMap[stepName];

    const config = step.internalService.config ?? {};
    const configEntries = Object.entries(config).filter(
      ([key]) =>
        key !== "endpoint" &&
        !key.toLowerCase().includes("endpoint") &&
        !key.toLowerCase().includes("url"),
    );
    const metadata = Object.fromEntries(configEntries);
    if (name === "vectordb") {
      metadata.USED_VECTOR_DB = usedVectorDb;
    }
    return [name, metadata];
  });
  const metadata = Object.fromEntries(metadataEntries);

  const serviceDetails: FetchedServiceDetails = {
    embedding: {},
    embedding_model_server: {},
    input_guard: {},
    llm: {},
    vllm: {},
    output_guard: {},
    reranker: {},
    reranker_model_server: {},
    prompt_template: {},
    retriever: {},
    vectordb: {},
  };
  for (const service in serviceDetails) {
    const details = metadata[service];
    const status = statuses[service];
    serviceDetails[service] = { status, details };
  }
  return serviceDetails;
};

export { parseServiceDetailsResponseData };
