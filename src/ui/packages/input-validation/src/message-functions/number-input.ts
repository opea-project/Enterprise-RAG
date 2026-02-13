// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { NumberInputRange } from "@/types";

export const getIsInRangeMessage = (range: NumberInputRange) =>
  `Enter number between ${range.min} and ${range.max}`;
