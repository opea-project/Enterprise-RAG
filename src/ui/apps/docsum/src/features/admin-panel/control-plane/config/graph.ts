// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceNodeData } from "@intel-enterprise-rag-ui/control-plane";
import { Edge, Node, Position } from "@xyflow/react";

const graphNodes: Node<ServiceNodeData>[] = [
  {
    id: "text_extractor",
    position: { x: 0, y: 0 },
    data: {
      id: "text_extractor",
      displayName: "Text Extractor",
      sourcePosition: Position.Right,
      selected: false,
    },
    type: "serviceNode",
    focusable: false,
    selectable: false,
  },
  {
    id: "text_compression",
    position: { x: 200, y: 0 },
    data: {
      id: "text_compression",
      displayName: "Text Compression",
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      selected: false,
    },
    type: "serviceNode",
    focusable: false,
    selectable: false,
  },

  {
    id: "text_splitter",
    position: { x: 400, y: 0 },
    data: {
      id: "text_splitter",
      displayName: "Text Splitter",
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      selected: false,
    },
    type: "serviceNode",
    focusable: false,
    selectable: false,
  },
  {
    id: "docsum",
    position: { x: 600, y: 0 },
    data: {
      id: "docsum",
      displayName: "DocSum",
      sourcePosition: Position.Bottom,
      targetPosition: Position.Left,
      selected: false,
    },
    type: "serviceNode",
    focusable: false,
    selectable: false,
  },
  {
    id: "llm",
    position: { x: 600, y: 144 },
    data: {
      id: "llm",
      displayName: "LLM",
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
      selected: false,
    },
    type: "serviceNode",
    focusable: false,
    selectable: false,
  },
  {
    id: "vllm",
    position: { x: 600, y: 288 },
    data: {
      id: "vllm",
      displayName: "vLLM Model Server",
      targetPosition: Position.Top,
      selected: false,
    },
    type: "serviceNode",
    focusable: false,
    selectable: false,
  },
];

const graphEdges: Edge[] = [
  {
    id: "text_extractor-text_compression",
    source: "text_extractor",
    target: "text_compression",
    selectable: false,
  },
  {
    id: "text_compression-text_splitter",
    source: "text_compression",
    target: "text_splitter",
    selectable: false,
  },
  {
    id: "text_splitter-docsum",
    source: "text_splitter",
    target: "docsum",
    selectable: false,
  },
  {
    id: "docsum-llm",
    source: "docsum",
    target: "llm",
    selectable: false,
  },
  {
    id: "llm-vllm",
    source: "llm",
    target: "vllm",
    selectable: false,
  },
];

export { graphEdges, graphNodes };
