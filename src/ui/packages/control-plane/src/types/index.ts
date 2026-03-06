// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Position } from "@xyflow/react";

import { LLMInputGuardArgs } from "@/configs/guards/llmInputGuard";
import { LLMOutputGuardArgs } from "@/configs/guards/llmOutputGuard";
import { LLMArgs } from "@/configs/services/llm";
import { PromptTemplateArgs } from "@/configs/services/promptTemplate";
import { RerankerArgs } from "@/configs/services/reranker";
import { RetrieverArgs } from "@/configs/services/retriever";

export enum ServiceStatus {
  Ready = "Ready",
  NotReady = "Not ready",
  NotAvailable = "Status Not Available",
}

export interface ServiceNodeData extends Record<string, unknown> {
  id: string;
  displayName: string;
  targetPosition?: Position;
  sourcePosition?: Position;
  additionalTargetPosition?: Position;
  additionalTargetId?: string;
  additionalSourcePosition?: Position;
  additionalSourceId?: string;
  selected?: boolean;
  status?: ServiceStatus;
  configurable?: boolean;
}

export type ServiceArgumentCheckboxValue = boolean;

export type ServiceArgumentNumberInputValue =
  | string
  | number
  | undefined
  | null;

export type ServiceArgumentSelectInputValue = string;

export type ServiceArgumentTextInputValue = string | string[] | null;

export type ServiceArgumentTextAreaValue = string;

export type ServiceArgumentInputValue =
  | ServiceArgumentCheckboxValue
  | ServiceArgumentNumberInputValue
  | ServiceArgumentSelectInputValue
  | ServiceArgumentTextInputValue
  | ServiceArgumentTextAreaValue;

export type OnArgumentValueChangeHandler = (
  argumentName: string,
  argumentValue: ServiceArgumentInputValue,
) => void;

export type OnArgumentValidityChangeHandler = (
  argumentName: string,
  isArgumentInvalid: boolean,
) => void;

export interface ServiceDetails {
  [key: string]: string | boolean | number;
}

export interface ServiceData extends ServiceNodeData {
  llmArgs?: LLMArgs;
  retrieverArgs?: RetrieverArgs;
  rerankerArgs?: RerankerArgs;
  promptTemplateArgs?: PromptTemplateArgs;
  inputGuardArgs?: LLMInputGuardArgs;
  outputGuardArgs?: LLMOutputGuardArgs;
  details?: ServiceDetails;
}
