// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface DataIngestionRequest {
  files?: { filename: string; data64: string }[];
  links?: string[];
}
