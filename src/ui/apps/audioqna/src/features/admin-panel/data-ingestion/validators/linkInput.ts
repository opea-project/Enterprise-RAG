// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { noInvalidCharacters } from "@intel-enterprise-rag-ui/input-validation";
import { string } from "yup";

import { LINK_ERROR_MESSAGE } from "@/features/admin-panel/data-ingestion/utils/constants";

const validationSchema = string()
  .required(LINK_ERROR_MESSAGE)
  .url(LINK_ERROR_MESSAGE)
  .matches(new RegExp("^https?://"), LINK_ERROR_MESSAGE)
  .test(
    "no-invalid-characters",
    "URL contains invalid characters. Please try again.",
    noInvalidCharacters(),
  );

export const validateLinkInput = async (value: string) =>
  await validationSchema.validate(value);
