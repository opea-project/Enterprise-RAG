// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AnyObject, object, string, TestFunction } from "yup";

import {
  containsRequiredValues,
  noEmpty,
} from "@/utils/validators/functions/textInput";

type PromptTemplateTestFunction = TestFunction<string | undefined, AnyObject>;

const requiredPlaceholders = ["{initial_query}", "{reranked_docs}"];
const placeholderRegex = /\{.*?\}/g;

const getContainsRequiredPlaceholdersErrorMessage = ({
  value,
}: {
  value: string;
}) => {
  const missingRequiredPlaceholders = [...requiredPlaceholders].filter(
    (requiredValue) => !value.includes(requiredValue),
  );
  return `Prompt Template is missing the following required placeholders: ${missingRequiredPlaceholders.join(", ")}`;
};

const containsAnyPlaceholders: PromptTemplateTestFunction = (value) => {
  if (value !== undefined) {
    const matchedPlaceholders = value.match(placeholderRegex);
    return matchedPlaceholders !== null && matchedPlaceholders.length > 0;
  } else {
    return false;
  }
};

const containsUnexpectedPlaceholders: PromptTemplateTestFunction = (value) => {
  if (value !== undefined) {
    const matchedPlaceholders = value.match(placeholderRegex);
    if (matchedPlaceholders !== null) {
      const unexpectedPlaceholders = matchedPlaceholders.filter(
        (match) => !requiredPlaceholders.includes(match),
      );
      return unexpectedPlaceholders.length === 0;
    } else {
      return false;
    }
  } else {
    return false;
  }
};

const containsRequiredPlaceholders: PromptTemplateTestFunction =
  containsRequiredValues(requiredPlaceholders);

const validationSchema = object().shape({
  promptTemplateInput: string()
    .test("not-empty", "Prompt Template cannot be empty", noEmpty(false))
    .test(
      "contains-any-placeholders",
      "Prompt Template does not contain any placeholders",
      containsAnyPlaceholders,
    )
    .test(
      "contains-unexpected-placeholders",
      "Prompt Template contains unexpected placeholders",
      containsUnexpectedPlaceholders,
    )
    .test(
      "contains-required-placeholders",
      getContainsRequiredPlaceholdersErrorMessage,
      containsRequiredPlaceholders,
    ),
});

export const validatePromptTemplateInput = async (value: string) =>
  await validationSchema.validate(value);
