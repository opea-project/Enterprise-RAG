// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  getIsInRangeMessage,
  isInRange,
  isValidNumber,
  NumberInputRange,
} from "@intel-enterprise-rag-ui/input-validation";
import { z } from "zod";

const createValidationSchema = (
  range: NumberInputRange,
  isNullable?: boolean,
) =>
  z.object({
    numberInput: z
      .string()
      .refine(isValidNumber, {
        message: "Enter a valid number value",
      })
      .refine(isInRange(range, isNullable), {
        message: getIsInRangeMessage(range),
      }),
  });

export const validateServiceArgumentNumberInput = async (
  value: string,
  range: NumberInputRange,
  isNullable?: boolean,
) => {
  const validationSchema = createValidationSchema(range, isNullable);
  return await validationSchema.parseAsync({ numberInput: value });
};
