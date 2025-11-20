// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { string } from "yup";

const validationSchema = string().required();

export const validateTextAreaInput = async (value: string) =>
  await validationSchema.validate(value);
