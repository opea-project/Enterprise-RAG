// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export type NumberInputRange = { min: number; max: number };

export type FileTestFunction = (value: File | undefined) => boolean;
export type FileArrayTestFunction = (
  value: (File | undefined)[] | undefined,
) => boolean;
