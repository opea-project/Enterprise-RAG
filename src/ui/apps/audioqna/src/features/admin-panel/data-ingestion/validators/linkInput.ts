// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { noInvalidCharacters } from "@intel-enterprise-rag-ui/input-validation";
import { z } from "zod";

import { LINK_ERROR_MESSAGE } from "@/features/admin-panel/data-ingestion/utils/constants";

const validationSchema = z
  .string({ required_error: LINK_ERROR_MESSAGE })
  .min(1, LINK_ERROR_MESSAGE)
  .url(LINK_ERROR_MESSAGE)
  .regex(new RegExp("^https?://"), LINK_ERROR_MESSAGE)
  .refine(noInvalidCharacters(), {
    message: "URL contains invalid characters. Please try again.",
  });

export const validateLinkInput = async (value: string) =>
  await validationSchema.parseAsync(value);
