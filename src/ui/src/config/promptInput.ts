// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

const maxRequestBodySize = 1 * 1024 * 1024; // 1MB in bytes - restriction from nginx config
const requestBodyFormatOverhead = '{ "text": "" }'.length;
export const promptMaxLength = maxRequestBodySize - requestBodyFormatOverhead;
export const promptMaxHeight = 15 * 16; // must be the same as max-height set for prompt-input css class
