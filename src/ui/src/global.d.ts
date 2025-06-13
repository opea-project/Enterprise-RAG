// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AppEnvKey } from "@/types/env";

declare global {
  interface Window {
    env: Record<AppEnvKey, string>;
  }
}
