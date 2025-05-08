// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { string } from "yup";

import { linkErrorMessage } from "@/features/admin-panel/data-ingestion/utils/constants";
import { notLinkToFile } from "@/features/admin-panel/data-ingestion/validators";
import { noInvalidCharacters } from "@/utils/validators/functions/textInput";

const validationSchema = string()
  .required(linkErrorMessage)
  .url(linkErrorMessage)
  .test(
    "no-invalid-characters",
    "URL contains invalid characters. Please try again.",
    noInvalidCharacters(),
  )
  .test(
    "not-link-to-file",
    "Only links to HTML files are supported.",
    notLinkToFile(),
  );

export const validateLinkInput = async (value: string) =>
  await validationSchema.validate(value);
