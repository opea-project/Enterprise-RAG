// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  containsSupportedCommaSeparatedValues,
  noEmpty,
} from "@intel-enterprise-rag-ui/input-validation";
import { object, string } from "yup";

const createValidationSchema = (
  isNullable?: boolean,
  isCommaSeparated?: boolean,
  supportedValues?: string[],
) =>
  object().shape({
    textInput: string()
      .test("no-empty", "This value cannot be empty", noEmpty(isNullable))
      .test(
        "should-contain-supported-values",
        "Only supported values are allowed. Check the tooltip for more details.",
        containsSupportedCommaSeparatedValues(
          isCommaSeparated,
          supportedValues,
        ),
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
  await validationSchema.validate({ textInput: value });
};
