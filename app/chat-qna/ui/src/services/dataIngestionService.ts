// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import endpoints from "@/api/endpoints.json";
import { LinkForIngestion } from "@/models/dataIngestion";
import { documentToBase64 } from "@/utils";

interface DataIngestionRequest {
  files?: { filename: string; data64: unknown }[];
  links?: string[];
}

class DataIngestionService {
  async postDataToIngest(documents: File[], links: LinkForIngestion[]) {
    const url = window.location.origin + endpoints.dataprep;
    const body: DataIngestionRequest = {};

    body.files = [];
    for (const document of documents) {
      const filename = document.name;
      const data64 = ((await documentToBase64(document)) as string).split(
        ",",
      )[1];

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
