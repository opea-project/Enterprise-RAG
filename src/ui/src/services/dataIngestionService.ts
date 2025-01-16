// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import endpoints from "@/api/endpoints.json";
import { LinkForIngestion } from "@/models/admin-panel/data-ingestion/dataIngestion";
import keycloakService from "@/services/keycloakService";

class DataIngestionService {
  async getLinks() {
    await keycloakService.refreshToken();

    const response = await fetch(endpoints.edp.getLinks, {
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch links");
    } else {
      return await response.json();
    }
  }

  async postLinks(linksForIngestion: LinkForIngestion[]) {
    await keycloakService.refreshToken();

    const url = endpoints.edp.postLinks;
    const links = linksForIngestion.map(({ value }) => value);
    const body = JSON.stringify({ links });

    const response = await fetch(url, {
      method: "POST",
      body,
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorResponse = await response.json();
      const errorMessage = errorResponse.detail ?? "Failed to post links";
      throw new Error(errorMessage);
    }
  }

  async retryLinkAction(uuid: string) {
    await keycloakService.refreshToken();

    const url = endpoints.edp.retryLinkAction.replace("{uuid}", uuid);
    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
      },
    });

    if (!response.ok) {
      const errorResponse = await response.json();
      const errorMessage =
        errorResponse.detail ?? "Error when retrying link action";
      throw new Error(errorMessage);
    }
  }

  async deleteLink(uuid: string) {
    await keycloakService.refreshToken();

    const url = `${endpoints.edp.deleteLink}/${uuid}`;
    const response = await fetch(url, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
      },
    });

    if (!response.ok) {
      const errorResponse = await response.json();
      const errorMessage = errorResponse.detail ?? "Error when deleting link";
      throw new Error(errorMessage);
    }
  }

  async getFiles() {
    await keycloakService.refreshToken();

    const response = await fetch(endpoints.edp.getFiles, {
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch links");
    } else {
      return await response.json();
    }
  }

  async getFilePresignedUrl(
    fileName: string,
    method: "GET" | "PUT" | "DELETE",
    bucketName: string = "default",
  ) {
    await keycloakService.refreshToken();

    const body = JSON.stringify({
      object_name: fileName,
      method,
      bucket_name: bucketName,
    });

    const response = await fetch(endpoints.edp.getPresignedUrl, {
      method: "POST",
      body,
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get presigned URL for file: ${fileName}`);
    }

    const { url } = await response.json();
    return url;
  }

  async postFiles(files: File[]) {
    await keycloakService.refreshToken();

    for (const file of files) {
      const method = "PUT";
      const url = await this.getFilePresignedUrl(file.name, method);

      const response = await fetch(url, {
        method,
        body: file,
        headers: {
          "Content-Type": file.type,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to upload file: ${file.name}`);
      }
    }
  }

  async retryFileAction(uuid: string) {
    await keycloakService.refreshToken();

    const url = endpoints.edp.retryFileAction.replace("{uuid}", uuid);
    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${keycloakService.getToken()}`,
      },
    });

    if (!response.ok) {
      const errorResponse = await response.json();
      const errorMessage =
        errorResponse.detail ?? "Error when retrying file action";
      throw new Error(errorMessage);
    }
  }

  async deleteFile(fileName: string) {
    await keycloakService.refreshToken();

    const method = "DELETE";
    const url = await this.getFilePresignedUrl(fileName, method);

    const response = await fetch(url, {
      method,
    });

    if (!response.ok) {
      throw new Error("Failed to delete file");
    }
  }
}

export default new DataIngestionService();
