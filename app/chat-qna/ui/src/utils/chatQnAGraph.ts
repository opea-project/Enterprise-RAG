// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Edge, Node, Position } from "@xyflow/react";

import { llmArguments } from "@/models/admin-panel/control-plane/llm";
import { rerankerArguments } from "@/models/admin-panel/control-plane/reranker";
import { ServiceData } from "@/models/admin-panel/control-plane/serviceData";
import { ServiceStatus } from "@/models/admin-panel/control-plane/serviceStatus";

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
    id: "llm_input_guard",
    position: { x: 640, y: 144 },
    data: {
      id: "llm_input_guard",
      displayName: "LLM Input Guard",
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      selected: false,
      status: ServiceStatus.Unknown,
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
    id: "llm_output_guard",
    position: { x: 1040, y: 144 },
    data: {
      id: "llm_output_guard",
      displayName: "LLM Output Guard",
      targetPosition: Position.Left,
      selected: false,
      status: ServiceStatus.Unknown,
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
    id: "reranker-llm_input_guard",
    source: "reranker",
    target: "llm_input_guard",
    selectable: false,
  },
  {
    id: "llm_input_guard-llm",
    source: "llm_input_guard",
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
    id: "llm-llm_output_guard",
    source: "llm",
    target: "llm_output_guard",
    selectable: false,
  },
];

export { graphEdges, graphNodes };
