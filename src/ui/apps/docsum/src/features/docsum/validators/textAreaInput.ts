// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { z } from "zod";

const validationSchema = z.string().min(1);

export const validateTextAreaInput = async (value: string) =>
  await validationSchema.parseAsync(value);
