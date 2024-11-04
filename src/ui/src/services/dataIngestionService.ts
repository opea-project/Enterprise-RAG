// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import endpoints from "@/api/endpoints.json";
import { DataIngestionRequest } from "@/api/models/dataIngestion";
import { LinkForIngestion } from "@/models/admin-panel/data-ingestion/dataIngestion";
import { documentToBase64 } from "@/utils";

class DataIngestionService {
  async postDataToIngest(documents: File[], links: LinkForIngestion[]) {
    const url = endpoints.dataprep;
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
