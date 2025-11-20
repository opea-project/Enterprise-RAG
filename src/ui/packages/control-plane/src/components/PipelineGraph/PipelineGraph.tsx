// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  Connection,
  ConnectionLineType,
  Controls,
  DefaultEdgeOptions,
  Edge,
  EdgeChange,
  FitViewOptions,
  MarkerType,
  Node,
  NodeChange,
  NodeTypes,
  OnSelectionChangeFunc,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import debounce from "lodash.debounce";
import { useEffect } from "react";

import ServiceNode from "@/components/ServiceNode/ServiceNode";

const defaultEdgeOptions: DefaultEdgeOptions = {
  animated: true,
  type: ConnectionLineType.Step,
  style: { strokeWidth: 2 },
  markerEnd: {
    type: MarkerType.ArrowClosed,
  },
};

const nodeTypes: NodeTypes = { serviceNode: ServiceNode };

interface PipelineGraphProps<
  T extends Record<string, unknown> = Record<string, unknown>,
> {
  nodes: Node<T>[];
  edges: Edge[];
  colorMode?: "light" | "dark";
  fitViewOptions?: FitViewOptions;
  onConnect?: (connection: Connection) => void;
  onEdgesChange?: (changes: EdgeChange[]) => void;
  onNodesChange?: (changes: NodeChange<Node<T>>[]) => void;
  onSelectionChange?: OnSelectionChangeFunc;
}

const PipelineGraphFlow = ({
  nodes,
  edges,
  colorMode,
  fitViewOptions = { padding: 0.5 },
  onConnect,
  onEdgesChange,
  onNodesChange,
  onSelectionChange,
}: PipelineGraphProps) => {
  // This hook can only be used inside component that is a child of ReactFlowProvider or ReactFlow component
  const reactFlowInstance = useReactFlow();

  useEffect(() => {
    const handleResize = debounce(() => {
      if (reactFlowInstance) {
        reactFlowInstance.fitView(fitViewOptions);
      }
    }, 300);

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      handleResize.cancel();
    };
  }, [fitViewOptions, reactFlowInstance]);

  return (
    <ReactFlow
      colorMode={colorMode}
      nodes={nodes}
      nodeTypes={nodeTypes}
      nodesConnectable={false}
      nodesFocusable={false}
      edges={edges}
      edgesFocusable={false}
      defaultEdgeOptions={defaultEdgeOptions}
      multiSelectionKeyCode={null}
      selectionOnDrag={false}
      selectNodesOnDrag={false}
      fitViewOptions={fitViewOptions}
      nodesDraggable={false}
      panOnDrag={false}
      panOnScroll={false}
      zoomOnScroll={false}
      zoomOnPinch={false}
      zoomOnDoubleClick={false}
      deleteKeyCode={null}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      onSelectionChange={onSelectionChange}
      fitView
    >
      <Controls showInteractive={false} fitViewOptions={fitViewOptions} />
    </ReactFlow>
  );
};

// ReactFlowProvider must wrap PipelineGraphFlow externally because useReactFlow is used inside PipelineGraphFlow
export const PipelineGraph = ({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onSelectionChange,
  colorMode,
  fitViewOptions = { padding: 0.5 },
}: PipelineGraphProps) => (
  <ReactFlowProvider>
    <PipelineGraphFlow
      colorMode={colorMode}
      nodes={nodes}
      edges={edges}
      fitViewOptions={fitViewOptions}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      onSelectionChange={onSelectionChange}
    />
  </ReactFlowProvider>
);
