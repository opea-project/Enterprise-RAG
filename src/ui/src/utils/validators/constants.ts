// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export const clientMaxBodySize = 64; // 64 MB - src/ui/default.conf - client_max_body_size 64m

// eslint-disable-next-line no-control-regex
export const nullCharsRegex = /(\x00|\u0000|\0|%00)/;

export const fileExtensionsWithoutMIMETypes: string[] = ["md", "jsonl", "yaml", "adoc"];
