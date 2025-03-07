// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  ConnectionLineType,
  Controls,
  type DefaultEdgeOptions,
  FitViewOptions,
  MarkerType,
  Node,
  NodeTypes,
  ReactFlow,
} from "@xyflow/react";
import { NodeChange } from "@xyflow/system";
import { useCallback } from "react";

import ServiceNode from "@/components/admin-panel/control-plane/ServiceNode/ServiceNode";
import { ServiceData } from "@/models/admin-panel/control-plane/serviceData";
import {
  chatQnAGraphEdgesSelector,
  chatQnAGraphNodesSelector,
  onChatQnAGraphConnect,
  onChatQnAGraphEdgesChange,
  onChatQnAGraphNodesChange,
  setChatQnAGraphSelectedServiceNode,
} from "@/store/chatQnAGraph.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import useColorScheme from "@/utils/hooks/useColorScheme";

const defaultEdgeOptions: DefaultEdgeOptions = {
  animated: true,
  type: ConnectionLineType.Step,
  style: { strokeWidth: 2 },
  markerEnd: {
    type: MarkerType.ArrowClosed,
  },
};

const nodeTypes: NodeTypes = { serviceNode: ServiceNode };

const ChatQnAGraph = () => {
  const dispatch = useAppDispatch();
  const nodes = useAppSelector(chatQnAGraphNodesSelector);
  const edges = useAppSelector(chatQnAGraphEdgesSelector);

  const { colorScheme } = useColorScheme();

  const handleSelectionChange = useCallback(
    ({ nodes }: { nodes: Node[] }) => {
      dispatch(
        setChatQnAGraphSelectedServiceNode(nodes as Node<ServiceData>[]),
      );
    },
    [dispatch],
  );

  const handleNodesChange = (changes: NodeChange<Node>[]) => {
    dispatch(
      onChatQnAGraphNodesChange(changes as NodeChange<Node<ServiceData>>[]),
    );
  };

  const fitViewOptions: FitViewOptions = {
    padding: nodes.length > 8 ? 0.27 : 0.8,
  };

  return (
    <ReactFlow
      colorMode={colorScheme}
      nodes={nodes}
      nodeTypes={nodeTypes}
      nodesConnectable={false}
      nodesFocusable={false}
      onNodesChange={handleNodesChange}
      edges={edges}
      edgesFocusable={false}
      onEdgesChange={onChatQnAGraphEdgesChange}
      onConnect={onChatQnAGraphConnect}
      defaultEdgeOptions={defaultEdgeOptions}
      multiSelectionKeyCode={null}
      selectionOnDrag={false}
      selectNodesOnDrag={false}
      onSelectionChange={handleSelectionChange}
      fitViewOptions={fitViewOptions}
      fitView
      nodesDraggable={false}
      panOnDrag={false}
      panOnScroll={false}
      zoomOnScroll={false}
      zoomOnPinch={false}
      zoomOnDoubleClick={false}
    >
      <Controls showInteractive={false} fitViewOptions={fitViewOptions} />
    </ReactFlow>
  );
};

export default ChatQnAGraph;
