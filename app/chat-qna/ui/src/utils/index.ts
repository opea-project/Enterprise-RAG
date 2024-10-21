import { ServiceDetailsResponse } from "@/api/models/serviceDetailsResponse";
import { FetchedServiceDetails } from "@/api/models/systemFingerprint";

const documentToBase64 = (document: File) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(document);
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
  });

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

  let usedVectorDb = "";
  const statusEntries = Object.entries(annotations)
    .filter(
      ([key]) =>
        key.startsWith("Deployment:apps/v1:") && !key.includes("router"),
    )
    .map(([key, value]) => {
      let name = key.split(":")[2].split("-")[0];
      if (name === "redis") {
        usedVectorDb = `${name.slice(0, 1)[0].toUpperCase()}${name.slice(1)}`;
        name = "vectordb";
      } else if (name === "tei") {
        name = "reranker_model_server";
      } else if (name === "torchserve") {
        name = "embedding_model_server";
      } else if (name === "reranking") {
        name = "reranker";
      }

      const status = value.split(";")[0];

      return [name, status];
    });
  const statuses = Object.fromEntries(statusEntries);

  const metadataEntries = steps.map((step) => {
    let name = step.name.toLowerCase();
    if (name === "teireranking") {
      name = "reranking_model_server";
    } else if (name === "torchserveembedding") {
      name = "embedding_model_server";
    } else if (name === "reranking") {
      name = "reranker";
    } else if (name === "reranking_model_server") {
      name = "reranker_model_server";
    }

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
    llm: {},
    reranker: {},
    reranker_model_server: {},
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

export { documentToBase64, parseServiceDetailsResponseData };
