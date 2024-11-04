// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceArgumentInputValue } from "@/models/admin-panel/control-plane/serviceArgument";
import { ServiceStatus } from "@/models/admin-panel/control-plane/serviceData";

export interface AppendArgumentsRequestBody {
  text: string;
}

export interface ScannerArguments {
  [argName: string]: null | number | string | boolean | string[];
}

export class GuardrailParams {
  [scannerName: string]: ScannerArguments;
}

export interface ServicesParameters {
  input_guardrail_params?: GuardrailParams;
  output_guardrail_params?: GuardrailParams;
  [key: string]: null | number | string | boolean | GuardrailParams | undefined;
}

export type ChangeArgumentsRequestData =
  | {
      [argumentName: string]: ServiceArgumentInputValue;
    }
  | GuardrailParams;

interface ServiceArgumentsToChange {
  name: string;
  data: ChangeArgumentsRequestData;
}

export type ChangeArgumentsRequestBody = ServiceArgumentsToChange[];

export interface FetchedServiceDetails {
  [serviceName: string]: {
    status?: ServiceStatus;
    details?: { [key: string]: string };
  };
}
