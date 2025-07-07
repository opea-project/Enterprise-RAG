// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { string } from "yup";

import { linkErrorMessage } from "@/features/admin-panel/data-ingestion/utils/constants";
import { noInvalidCharacters } from "@/utils/validators/functions/textInput";

const validationSchema = string()
  .required(linkErrorMessage)
  .url(linkErrorMessage)
  .matches(new RegExp("^https?://"), linkErrorMessage)
  .test(
    "no-invalid-characters",
    "URL contains invalid characters. Please try again.",
    noInvalidCharacters(),
  );

export const validateLinkInput = async (value: string) =>
  await validationSchema.validate(value);
