// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  containsSupportedCommaSeparatedValues,
  noEmpty,
} from "@intel-enterprise-rag-ui/input-validation";
import { z } from "zod";

const createValidationSchema = (
  isNullable?: boolean,
  isCommaSeparated?: boolean,
  supportedValues?: string[],
) =>
  z.object({
    textInput: z
      .string()
      .refine(noEmpty(isNullable), {
        message: "This value cannot be empty",
      })
      .refine(
        containsSupportedCommaSeparatedValues(
          isCommaSeparated,
          supportedValues,
        ),
        {
          message:
            "Only supported values are allowed. Check the tooltip for more details.",
        },
      ),
  });

export const validateServiceArgumentTextInput = async (
  value: string,
  isNullable?: boolean,
  isCommaSeparated?: boolean,
  supportedValues?: string[],
) => {
  const validationSchema = createValidationSchema(
    isNullable,
    isCommaSeparated,
    supportedValues,
  );
  await validationSchema.parseAsync({ textInput: value });
};
