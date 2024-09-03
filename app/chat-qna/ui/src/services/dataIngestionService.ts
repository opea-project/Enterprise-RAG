// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { LinkForIngestion } from "@/models/dataIngestion";
import { documentToBase64 } from "@/utils";

const DATA_INGESTION_SERVICE_URL = import.meta.env.VITE_DATA_INGESTION_URL;
const DATA_INGESTION_ENDPOINT = "/v1/dataprep";

interface DataIngestionRequest {
  files?: { filename: string; data64: unknown }[];
  links?: string[];
}

class DataIngestionService {
  async postDataToIngest(documents: File[], links: LinkForIngestion[]) {
    const url = DATA_INGESTION_SERVICE_URL + DATA_INGESTION_ENDPOINT;
    const body: DataIngestionRequest = {};

    body.files = [];
    for (const document of documents) {
      const filename = document.name;
      const data64 = await documentToBase64(document);

      body.files.push({
        filename,
        data64,
      });
    }

    body.links = links.map(({ value }) => value);

    return fetch(url, {
      method: "POST",
      body: JSON.stringify(body),
      headers: {
        Authorization: `Bearer ${sessionStorage.getItem("token")}`,
      },
    });
  }
}

export default new DataIngestionService();
