// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Position } from "@xyflow/react";

import { ServiceArgumentCheckboxValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import { ServiceArgumentNumberInputValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentSelectInputValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import { ServiceArgumentTextInputValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentTextInput/ServiceArgumentTextInput";
import { ServiceArgumentThreeStateSwitchValue } from "@/features/admin-panel/control-plane/components/ServiceArgumentThreeStateSwitch/ServiceArgumentThreeStateSwitch";
import { LLMInputGuardArgs } from "@/features/admin-panel/control-plane/config/guards/llmInputGuard";
import { LLMOutputGuardArgs } from "@/features/admin-panel/control-plane/config/guards/llmOutputGuard";
import { LLMArgs } from "@/features/admin-panel/control-plane/config/llm";
import { RerankerArgs } from "@/features/admin-panel/control-plane/config/reranker";
import { RetrieverArgs } from "@/features/admin-panel/control-plane/config/retriever";

export type ServiceArgumentInputValue =
  | ServiceArgumentCheckboxValue
  | ServiceArgumentNumberInputValue
  | ServiceArgumentSelectInputValue
  | ServiceArgumentTextInputValue
  | ServiceArgumentThreeStateSwitchValue;

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

export enum ServiceStatus {
  Ready = "Ready",
  NotReady = "Not ready",
  NotAvailable = "Status Not Available",
}

export interface ServiceData extends Record<string, unknown> {
  id: string;
  displayName: string;
  llmArgs?: LLMArgs;
  retrieverArgs?: RetrieverArgs;
  rerankerArgs?: RerankerArgs;
  promptTemplate?: string;
  inputGuardArgs?: LLMInputGuardArgs;
  outputGuardArgs?: LLMOutputGuardArgs;
  details?: ServiceDetails;
  targetPosition?: Position;
  sourcePosition?: Position;
  additionalTargetPosition?: Position;
  additionalTargetId?: string;
  additionalSourcePosition?: Position;
  additionalSourceId?: string;
  selected?: boolean;
  status?: ServiceStatus;
}
