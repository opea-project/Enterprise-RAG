// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

type ServiceArgumentType = "text" | "number" | "boolean";

export type ServiceArgumentInputValue = string | number | boolean | null;

type ServiceArgumentValue = ServiceArgumentInputValue | string[];

type ServiceArgumentRange = { min: number; max: number };

export default interface ServiceArgument {
  displayName: string;
  range?: ServiceArgumentRange;
  value: ServiceArgumentValue;
  type?: ServiceArgumentType;
  nullable?: boolean;
  commaSeparated?: boolean;
}
