// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

type ServiceArgumentType = "text" | "number" | "boolean";

export default interface ServiceArgument {
  displayName: string;
  range?: { min: number; max: number };
  value: string | number | boolean | null;
  type?: ServiceArgumentType;
  nullable?: boolean;
}
