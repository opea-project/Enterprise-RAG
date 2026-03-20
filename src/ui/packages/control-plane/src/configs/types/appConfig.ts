// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { llmInputGuardFormConfig } from "@/configs/guards/llmInputGuard";
import { llmOutputGuardFormConfig } from "@/configs/guards/llmOutputGuard";
import { llmFormConfig } from "@/configs/services/llm";
import { promptTemplateFormConfig } from "@/configs/services/promptTemplate";
import { rerankerFormConfig } from "@/configs/services/reranker";
import { retrieverFormConfig } from "@/configs/services/retriever";

/**
 * Application-specific control plane configuration
 */
export interface AppControlPlaneConfig {
  /**
   * Services to enable and their config overrides
   */
  services?: {
    llm?: {
      enabled: boolean;
      configOverrides?: Partial<typeof llmFormConfig>;
    };
    reranker?: {
      enabled: boolean;
      configOverrides?: Partial<typeof rerankerFormConfig>;
    };
    retriever?: {
      enabled: boolean;
      configOverrides?: Partial<typeof retrieverFormConfig>;
    };
    promptTemplate?: {
      enabled: boolean;
      configOverrides?: Partial<typeof promptTemplateFormConfig>;
    };
  };

  /**
   * Guards to enable and their scanner configurations
   */
  guards?: {
    inputGuard?: {
      enabled: boolean;
      enabledScanners?: (keyof typeof llmInputGuardFormConfig)[];
      configOverrides?: Partial<typeof llmInputGuardFormConfig>;
    };
    outputGuard?: {
      enabled: boolean;
      enabledScanners?: (keyof typeof llmOutputGuardFormConfig)[];
      configOverrides?: Partial<typeof llmOutputGuardFormConfig>;
    };
  };
}

/**
 * Default configurations for all services
 */
export const defaultServiceConfigs = {
  llm: llmFormConfig,
  reranker: rerankerFormConfig,
  retriever: retrieverFormConfig,
  promptTemplate: promptTemplateFormConfig,
};

/**
 * Default configurations for all guards
 */
export const defaultGuardConfigs = {
  inputGuard: llmInputGuardFormConfig,
  outputGuard: llmOutputGuardFormConfig,
};

/**
 * Helper to create a control plane config with defaults
 */
export function createControlPlaneConfig(
  config: AppControlPlaneConfig,
): AppControlPlaneConfig {
  return {
    services: {
      llm: { enabled: true, ...config.services?.llm },
      reranker: { enabled: true, ...config.services?.reranker },
      retriever: { enabled: true, ...config.services?.retriever },
      promptTemplate: { enabled: true, ...config.services?.promptTemplate },
    },
    guards: {
      inputGuard: { enabled: true, ...config.guards?.inputGuard },
      outputGuard: { enabled: true, ...config.guards?.outputGuard },
    },
  };
}
