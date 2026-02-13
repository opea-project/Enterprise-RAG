// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface GetFilePresignedUrlRequest {
  fileName: string;
  method: GetFilePresignedUrlMethod;
  bucketName: string;
}

type GetFilePresignedUrlMethod = "GET" | "PUT" | "DELETE";

export interface DownloadFileRequest {
  presignedUrl: string;
  fileName: string;
}
