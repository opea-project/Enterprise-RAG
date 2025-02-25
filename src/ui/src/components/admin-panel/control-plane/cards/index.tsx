// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import EmbeddingCard from "@/components/admin-panel/control-plane/cards/EmbeddingCard";
import EmbeddingModelServerCard from "@/components/admin-panel/control-plane/cards/EmbeddingModelServerCard";
import LLMCard from "@/components/admin-panel/control-plane/cards/LLMCard";
import LLMInputGuardCard from "@/components/admin-panel/control-plane/cards/LLMInputGuardCard";
import LLMOutputGuardCard from "@/components/admin-panel/control-plane/cards/LLMOutputGuardCard";
import PromptTemplateCard from "@/components/admin-panel/control-plane/cards/PromptTemplateCard";
import RerankerCard from "@/components/admin-panel/control-plane/cards/RerankerCard";
import RerankerModelServerCard from "@/components/admin-panel/control-plane/cards/RerankerModelServerCard";
import RetrieverCard from "@/components/admin-panel/control-plane/cards/RetrieverCard";
import VectorDBCard from "@/components/admin-panel/control-plane/cards/VectorDBCard";
import VLLMModelServerCard from "@/components/admin-panel/control-plane/cards/VLLMModelServerCard";
import { ServiceData } from "@/types/admin-panel/control-plane";

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
