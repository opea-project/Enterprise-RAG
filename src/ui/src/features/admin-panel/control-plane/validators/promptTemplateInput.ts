// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AnyObject, object, string, TestFunction } from "yup";

import { PromptTemplateArgs } from "@/features/admin-panel/control-plane/config/chat-qna-graph/prompt-template";
import {
  containsRequiredValues,
  noEmpty,
} from "@/utils/validators/functions/textInput";

type PromptTemplateTestFunction = TestFunction<string | undefined, AnyObject>;

const requiredPlaceholders = [
  "{user_prompt}",
  "{reranked_docs}",
  "{conversation_history}",
];
const placeholderRegex = /\{.*?\}/g;

const getContainsRequiredPlaceholdersErrorMessage = ({
  value,
}: {
  value: string;
}) => {
  const missingRequiredPlaceholders = [...requiredPlaceholders].filter(
    (requiredValue) => !value.includes(requiredValue),
  );
  return `Prompt Templates are missing the following required placeholders: ${missingRequiredPlaceholders.join(", ")}`;
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

const containsDuplicatePlaceholders: PromptTemplateTestFunction = (value) => {
  if (value !== undefined) {
    const matchedPlaceholders = value.match(placeholderRegex);
    if (matchedPlaceholders !== null) {
      const uniquePlaceholders = new Set(matchedPlaceholders);
      return uniquePlaceholders.size === matchedPlaceholders.length;
    } else {
      return false;
    }
  } else {
    return false;
  }
};

const validationSchema = object().shape({
  user: string().test(
    "not-empty",
    "User Prompt Template cannot be empty",
    noEmpty(false),
  ),
  system: string().test(
    "not-empty",
    "System Prompt Template cannot be empty",
    noEmpty(false),
  ),
  joined: string()
    .test("not-empty", "Prompt Templates cannot be empty", noEmpty(false))
    .test(
      "contains-any-placeholders",
      "Prompt Templates do not contain any placeholders",
      containsAnyPlaceholders,
    )
    .test(
      "contains-unexpected-placeholders",
      "Prompt Templates contain unexpected placeholders",
      containsUnexpectedPlaceholders,
    )
    .test(
      "contains-required-placeholders",
      getContainsRequiredPlaceholdersErrorMessage,
      containsRequiredPlaceholders,
    )
    .test(
      "contains-duplicated-placeholders",
      "Prompt Templates contain duplicated placeholders",
      containsDuplicatePlaceholders,
    ),
});

export const validatePromptTemplateForm = async (
  templates: PromptTemplateArgs,
) => {
  const joinedTemplates = Object.values(templates).join("");
  await validationSchema.validate({
    user: templates.user_prompt_template,
    system: templates.system_prompt_template,
    joined: joinedTemplates,
  });
};
