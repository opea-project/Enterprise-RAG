// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import EmbeddingCard from "@/features/admin-panel/control-plane/components/cards/EmbeddingCard";
import EmbeddingModelServerCard from "@/features/admin-panel/control-plane/components/cards/EmbeddingModelServerCard";
import LLMCard from "@/features/admin-panel/control-plane/components/cards/LLMCard";
import LLMInputGuardCard from "@/features/admin-panel/control-plane/components/cards/LLMInputGuardCard";
import LLMOutputGuardCard from "@/features/admin-panel/control-plane/components/cards/LLMOutputGuardCard";
import PromptTemplateCard from "@/features/admin-panel/control-plane/components/cards/PromptTemplateCard";
import RerankerCard from "@/features/admin-panel/control-plane/components/cards/RerankerCard";
import RerankerModelServerCard from "@/features/admin-panel/control-plane/components/cards/RerankerModelServerCard";
import RetrieverCard from "@/features/admin-panel/control-plane/components/cards/RetrieverCard";
import VectorDBCard from "@/features/admin-panel/control-plane/components/cards/VectorDBCard";
import VLLMModelServerCard from "@/features/admin-panel/control-plane/components/cards/VLLMModelServerCard";
import { ServiceData } from "@/features/admin-panel/control-plane/types";

export const cards = {
  embedding_model_server: EmbeddingModelServerCard,
  embedding: EmbeddingCard,
  retriever: RetrieverCard,
  vectordb: VectorDBCard,
  reranker: RerankerCard,
  prompt_template: PromptTemplateCard,
  reranker_model_server: RerankerModelServerCard,
  input_guard: LLMInputGuardCard,
  llm: LLMCard,
  vllm: VLLMModelServerCard,
  output_guard: LLMOutputGuardCard,
};

export type SelectedServiceId = keyof typeof cards;

export interface ControlPlaneCardProps {
  data: ServiceData;
}
