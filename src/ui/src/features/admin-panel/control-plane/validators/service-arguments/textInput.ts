// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { object, string } from "yup";

import { noEmpty } from "@/utils/validators/functions/textInput";

const createValidationSchema = (isNullable?: boolean) =>
  object().shape({
    textInput: string().test(
      "no-empty",
      "This value cannot be empty",
      noEmpty(isNullable),
    ),
  });

export const validateServiceArgumentTextInput = async (
  value: string,
  isNullable?: boolean,
) => {
  const validationSchema = createValidationSchema(isNullable);
  await validationSchema.validate({ textInput: value });
};
