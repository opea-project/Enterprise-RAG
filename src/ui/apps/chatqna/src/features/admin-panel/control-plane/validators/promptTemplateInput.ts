// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  containsRequiredValues,
  noEmpty,
} from "@intel-enterprise-rag-ui/input-validation";
import { z } from "zod";

import { PromptTemplateArgs } from "@/features/admin-panel/control-plane/config/chat-qna-graph/promptTemplate";

type PromptTemplateTestFunction = (value: string | undefined) => boolean;

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

const validationSchema = z.object({
  user: z.string().refine(noEmpty(false), {
    message: "User Prompt Template cannot be empty",
  }),
  system: z.string().refine(noEmpty(false), {
    message: "System Prompt Template cannot be empty",
  }),
  joined: z
    .string()
    .refine(noEmpty(false), {
      message: "Prompt Templates cannot be empty",
    })
    .refine(containsAnyPlaceholders, {
      message: "Prompt Templates do not contain any placeholders",
    })
    .refine(containsUnexpectedPlaceholders, {
      message: "Prompt Templates contain unexpected placeholders",
    })
    .refine(containsRequiredPlaceholders, (joined) => ({
      message: getContainsRequiredPlaceholdersErrorMessage({ value: joined }),
    }))
    .refine(containsDuplicatePlaceholders, {
      message: "Prompt Templates contain duplicated placeholders",
    }),
});

export const validatePromptTemplateForm = async (
  templates: PromptTemplateArgs,
) => {
  const joinedTemplates = Object.values(templates).join("");
  await validationSchema.parseAsync({
    user: templates.user_prompt_template,
    system: templates.system_prompt_template,
    joined: joinedTemplates,
  });
};
