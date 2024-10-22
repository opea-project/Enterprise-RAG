// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Edge, Node, Position } from "@xyflow/react";

import { inputGuardArguments } from "@/models/admin-panel/control-plane/guardrails/inputGuard";
import { outputGuardArguments } from "@/models/admin-panel/control-plane/guardrails/outputGuard";
import { llmArguments } from "@/models/admin-panel/control-plane/llm";
import { rerankerArguments } from "@/models/admin-panel/control-plane/reranker";
import { ServiceData } from "@/models/admin-panel/control-plane/serviceData";

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
      args: rerankerArguments,
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
    id: "input_guard",
    position: { x: 640, y: 144 },
    data: {
      id: "input_guard",
      displayName: "LLM Input Guard",
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      selected: false,
      guardArgs: inputGuardArguments,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "llm",
    position: { x: 840, y: 144 },
    data: {
      id: "llm",
      displayName: "LLM",
      args: llmArguments,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      additionalSourcePosition: Position.Bottom,
      additionalSourceId: "llm-llm_model_server-source",
      selected: false,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "llm_model_server",
    position: { x: 840, y: 288 },
    data: {
      id: "llm_model_server",
      displayName: "LLM Model Server",
      targetPosition: Position.Top,
      selected: false,
    },
    type: "serviceNode",
    focusable: true,
  },
  {
    id: "output_guard",
    position: { x: 1040, y: 144 },
    data: {
      id: "output_guard",
      displayName: "LLM Output Guard",
      targetPosition: Position.Left,
      selected: false,
      guardArgs: outputGuardArguments,
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
    id: "reranker-llm",
    source: "reranker",
    target: "llm",
    selectable: false,
  },
  {
    id: "reranker-input_guard",
    source: "reranker",
    target: "input_guard",
    selectable: false,
  },
  {
    id: "input_guard-llm",
    source: "input_guard",
    target: "llm",
    selectable: false,
  },
  {
    id: "llm-llm_model_server",
    source: "llm",
    target: "llm_model_server",
    sourceHandle: "llm-llm_model_server-source",
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
