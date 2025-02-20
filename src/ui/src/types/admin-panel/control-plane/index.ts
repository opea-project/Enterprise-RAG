// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Position } from "@xyflow/react";

import { ServiceArgumentCheckboxValue } from "@/components/admin-panel/control-plane/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import { ServiceArgumentNumberInputValue } from "@/components/admin-panel/control-plane/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentSelectInputValue } from "@/components/admin-panel/control-plane/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import { ServiceArgumentTextInputValue } from "@/components/admin-panel/control-plane/ServiceArgumentTextInput/ServiceArgumentTextInput";
import { ServiceArgumentThreeStateSwitchValue } from "@/components/admin-panel/control-plane/ServiceArgumentThreeStateSwitch/ServiceArgumentThreeStateSwitch";
import { LLMInputGuardArgs } from "@/config/control-plane/guards/llmInputGuard";
import { LLMOutputGuardArgs } from "@/config/control-plane/guards/llmOutputGuard";
import { LLMArgs } from "@/config/control-plane/llm";
import { RerankerArgs } from "@/config/control-plane/reranker";
import { RetrieverArgs } from "@/config/control-plane/retriever";

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
