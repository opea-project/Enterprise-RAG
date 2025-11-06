// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  getIsInRangeMessage,
  isInRange,
  isValidNumber,
  NumberInputRange,
} from "@intel-enterprise-rag-ui/input-validation";
import { object, string } from "yup";

const createValidationSchema = (
  range: NumberInputRange,
  isNullable?: boolean,
) =>
  object().shape({
    numberInput: string()
      .test("is-valid-number", "Enter a valid number value", isValidNumber)
      .test(
        "is-in-range",
        getIsInRangeMessage(range),
        isInRange(range, isNullable),
      ),
  });

export const validateServiceArgumentNumberInput = async (
  value: string,
  range: NumberInputRange,
  isNullable?: boolean,
) => {
  const validationSchema = createValidationSchema(range, isNullable);
  return await validationSchema.validate({ numberInput: value });
};
