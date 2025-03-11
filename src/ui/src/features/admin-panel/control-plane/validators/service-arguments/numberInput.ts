// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { object, string } from "yup";

import {
  isInRange,
  isValidNumber,
} from "@/utils/validators/functions/numberInput";
import { NumberInputRange } from "@/utils/validators/types";

const createValidationSchema = (range: NumberInputRange, nullable?: boolean) =>
  object().shape({
    numberInput: string()
      .test("is-valid-number", "Enter a valid number value", isValidNumber)
      .test(
        "is-in-range",
        `Enter number between ${range.min} and ${range.max}`,
        isInRange(range, nullable),
      ),
  });

export const validateServiceArgumentNumberInput = async (
  value: string,
  range: NumberInputRange,
  nullable?: boolean,
) => {
  const validationSchema = createValidationSchema(range, nullable);
  return await validationSchema.validate({ numberInput: value });
};
