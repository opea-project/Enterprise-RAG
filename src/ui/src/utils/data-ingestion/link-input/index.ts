// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import * as Yup from "yup";

import { noInvalidCharacters } from "@/utils/validators/textInput";

const GENERAL_ERROR_MSG =
  "Please enter valid URL that starts with protocol (http:// or https://).";

const INVALID_CHARACTERS_MSG =
  "URL contains invalid characters. Please try again.";

const validationSchema = Yup.string()
  .required(GENERAL_ERROR_MSG)
  .url(GENERAL_ERROR_MSG)
  .test("no-invalid-characters", INVALID_CHARACTERS_MSG, noInvalidCharacters());

const validateLinkInput = async (value: string) =>
  await validationSchema.validate(value);

export { validateLinkInput };
