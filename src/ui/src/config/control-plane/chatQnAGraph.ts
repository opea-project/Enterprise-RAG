// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Edge, Node, Position } from "@xyflow/react";

import { llmInputGuardArgumentsDefault } from "@/config/control-plane/guards/llmInputGuard";
import { llmOutputGuardArgumentsDefault } from "@/config/control-plane/guards/llmOutputGuard";
import { llmArgumentsDefault } from "@/config/control-plane/llm";
import { rerankerArgumentsDefault } from "@/config/control-plane/reranker";
import { retrieverArgumentsDefault } from "@/config/control-plane/retriever";
import { ServiceData } from "@/types/admin-panel/control-plane";

export const LLM_NODE_POSITION_NO_GUARDS = { x: 840, y: 144 };
export const VLLM_NODE_POSITION_NO_GUARDS = { x: 840, y: 288 };

const graphNodes: Node<ServiceData>[] = [
  {
    id: "embedding_model_server",
    position: { x: 40, y: 288 },
    data: {
      id: "embedding_model_server",
      displayName: "Embedding Model Server",
      targetPosition: Position.Top,
      selected: false,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "embedding",
    position: { x: 40, y: 144 },
    data: {
      id: "embedding",
      displayName: "Embedding",
      sourcePosition: Position.Right,
      additionalSourcePosition: Position.Bottom,
      additionalSourceId: "embedding-embedding_model_server-source",
      selected: false,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "retriever",
    position: { x: 240, y: 144 },
    data: {
      id: "retriever",
      displayName: "Retriever",
      retrieverArgs: retrieverArgumentsDefault,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      additionalTargetPosition: Position.Top,
      additionalTargetId: "retriever-vectordb-target",
      selected: false,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "vectordb",
    position: { x: 240, y: 0 },
    data: {
      id: "vectordb",
      displayName: "VectorDB",
      sourcePosition: Position.Bottom,
      selected: false,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "reranker",
    position: { x: 440, y: 144 },
    data: {
      id: "reranker",
      displayName: "Reranker",
      rerankerArgs: rerankerArgumentsDefault,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      additionalSourcePosition: Position.Bottom,
      additionalSourceId: "reranker-reranker_model_server-source",
      selected: false,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "reranker_model_server",
    position: { x: 440, y: 288 },
    data: {
      id: "reranker_model_server",
      displayName: "Reranker Model Server",
      targetPosition: Position.Top,
      selected: false,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "prompt_template",
    position: { x: 640, y: 144 },
    data: {
      id: "prompt_template",
      displayName: "Prompt Template",
      promptTemplate: "",
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      selected: false,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "input_guard",
    position: { x: 840, y: 144 },
    data: {
      id: "input_guard",
      displayName: "LLM Input Guard",
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      selected: false,
      inputGuardArgs: llmInputGuardArgumentsDefault,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "llm",
    position: { x: 1040, y: 144 },
    data: {
      id: "llm",
      displayName: "LLM",
      llmArgs: llmArgumentsDefault,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      additionalSourcePosition: Position.Bottom,
      additionalSourceId: "llm-vllm-source",
      selected: false,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "vllm",
    position: { x: 1040, y: 288 },
    data: {
      id: "vllm",
      displayName: "vLLM Model Server",
      targetPosition: Position.Top,
      selected: false,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "output_guard",
    position: { x: 1240, y: 144 },
    data: {
      id: "output_guard",
      displayName: "LLM Output Guard",
      targetPosition: Position.Left,
      selected: false,
      outputGuardArgs: llmOutputGuardArgumentsDefault,
    },
    type: "serviceNode",
    focusable: true,
  },
];

const graphEdges: Edge[] = [
  {
    id: "embedding-embedding_model_server",
    target: "embedding_model_server",
    source: "embedding",
    sourceHandle: "embedding-embedding_model_server-source",
    selectable: false,
  },
  {
    id: "embedding-retriever",
    source: "embedding",
    target: "retriever",
    selectable: false,
  },
  {
    id: "vectordb-retriever",
    source: "vectordb",
    target: "retriever",
    targetHandle: "retriever-vectordb-target",
    selectable: false,
  },
  {
    id: "retriever-reranker",
    source: "retriever",
    target: "reranker",
    selectable: false,
  },
  {
    id: "reranker-reranker_model_server",
    source: "reranker",
    target: "reranker_model_server",
    sourceHandle: "reranker-reranker_model_server-source",
    selectable: false,
  },
  {
    id: "reranker-prompt_template",
    source: "reranker",
    target: "prompt_template",
    selectable: false,
  },
  {
    id: "prompt_template-input_guard",
    source: "prompt_template",
    target: "input_guard",
    selectable: false,
  },
  {
    id: "prompt_template-llm",
    source: "prompt_template",
    target: "llm",
    selectable: false,
  },
  {
    id: "input_guard-llm",
    source: "input_guard",
    target: "llm",
    selectable: false,
  },
  {
    id: "llm-vllm",
    source: "llm",
    target: "vllm",
    sourceHandle: "llm-vllm-source",
    selectable: false,
  },
  {
    id: "llm-output_guard",
    source: "llm",
    target: "output_guard",
    selectable: false,
  },
];

export { graphEdges, graphNodes };
