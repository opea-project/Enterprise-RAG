// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AnyObject, TestFunction, ValidateOptions } from "yup";

export type NumberInputRange = { min: number; max: number };

export type FileTestFunction = TestFunction<File | undefined, AnyObject>;
export type FileArrayTestFunction = TestFunction<
  (File | undefined)[] | undefined,
  ValidateOptions<{ clientMaxBodySize?: number }>
>;
