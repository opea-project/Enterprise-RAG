// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Edge, Node, Position } from "@xyflow/react";

import { inputGuardArguments } from "@/models/admin-panel/control-plane/guardrails/inputGuard";
import { outputGuardArguments } from "@/models/admin-panel/control-plane/guardrails/outputGuard";
import { llmArguments } from "@/models/admin-panel/control-plane/llm";
import { rerankerArguments } from "@/models/admin-panel/control-plane/reranker";
import {
  ServiceData,
  ServiceStatus,
} from "@/models/admin-panel/control-plane/serviceData";

const graphNodes: Node<ServiceData>[] = [
  {
    id: "embedding_model_server",
    position: { x: 40, y: 288 },
    data: {
      id: "embedding_model_server",
      displayName: "Embedding Model Server",
      sourcePosition: Position.Top,
      selected: false,
      status: ServiceStatus.Unknown,
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
      targetPosition: Position.Bottom,
      sourcePosition: Position.Right,
      selected: false,
      status: ServiceStatus.Unknown,
      details: {
        "Model Name": "MODEL_NAME",
        "Model Server Name": "MODEL_SERVER_NAME",
        "Vector Size": "VECTOR_SIZE",
        "Connector Used": "CONNECTOR_USED",
      },
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
      details: {
        "Used Vector DB": "USED_VECTOR_DB",
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      additionalTargetPosition: Position.Top,
      additionalTargetId: "retriever-vectordb-target",
      selected: false,
      status: ServiceStatus.Unknown,
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
      status: ServiceStatus.Unknown,
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
      details: {
        "Model Name": "MODEL_NAME_PLACEHOLDER",
        "Model Server Name": "MODEL_SERVER_NAME",
        "Vector Size": "VECTOR_SIZE",
        "Connector Used": "CONNECTOR_USER",
      },
      args: rerankerArguments,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      additionalTargetPosition: Position.Bottom,
      additionalTargetId: "reranker-model-server-target",
      selected: false,
      status: ServiceStatus.Unknown,
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
      sourcePosition: Position.Top,
      selected: false,
      status: ServiceStatus.Unknown,
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
      status: ServiceStatus.Unknown,
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
      details: {
        "Model Name": "MODEL_NAME",
        "Model Server Name": "MODEL_SERVER_NAME",
        "Connector Used": "CONNECTOR_USED",
      },
      args: llmArguments,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      additionalTargetPosition: Position.Bottom,
      additionalTargetId: "llm-model-server-target",
      selected: false,
      status: ServiceStatus.Unknown,
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
      sourcePosition: Position.Top,
      selected: false,
      status: ServiceStatus.Unknown,
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
      status: ServiceStatus.Unknown,
      guardArgs: outputGuardArguments,
    },
    type: "serviceNode",
    focusable: true,
  },
];

const graphEdges: Edge[] = [
  {
    id: "embedding_model_server-embedding",
    source: "embedding_model_server",
    target: "embedding",
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
    id: "reranker_model_server-reranker",
    source: "reranker_model_server",
    target: "reranker",
    targetHandle: "reranker-model-server-target",
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
    id: "llm_model_server-llm",
    source: "llm_model_server",
    target: "llm",
    targetHandle: "llm-model-server-target",
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
