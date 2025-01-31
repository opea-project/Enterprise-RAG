// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { string } from "yup";

import { noInvalidCharacters } from "@/utils/validators/textInput";

export const urlErrorMessage =
  "Enter valid URL that starts with protocol (http:// or https://).";

const urlInvalidCharactersMsg =
  "URL contains invalid characters. Please try again.";

const validationSchema = string()
  .required(urlErrorMessage)
  .url(urlErrorMessage)
  .test(
    "no-invalid-characters",
    urlInvalidCharactersMsg,
    noInvalidCharacters(),
  );

const validateLinkInput = async (value: string) =>
  await validationSchema.validate(value);

export { validateLinkInput };
