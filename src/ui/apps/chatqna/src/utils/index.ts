// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getAppEnv } from "@intel-enterprise-rag-ui/utils";

import { AppEnvKey } from "@/types";

export const getChatQnAAppEnv = (envKey: AppEnvKey) =>
  getAppEnv(import.meta.env, window, envKey);
