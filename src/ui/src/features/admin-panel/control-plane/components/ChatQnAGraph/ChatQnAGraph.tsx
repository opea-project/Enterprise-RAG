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

import ServiceNode from "@/features/admin-panel/control-plane/components/ServiceNode/ServiceNode";
import {
  chatQnAGraphEdgesSelector,
  chatQnAGraphNodesSelector,
  onChatQnAGraphConnect,
  onChatQnAGraphEdgesChange,
  onChatQnAGraphNodesChange,
  setChatQnAGraphIsEditModeEnabled,
  setChatQnAGraphSelectedServiceNode,
} from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { ServiceData } from "@/features/admin-panel/control-plane/types";
import useColorScheme from "@/hooks/useColorScheme";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

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
      dispatch(setChatQnAGraphIsEditModeEnabled(false));
      dispatch(
        setChatQnAGraphSelectedServiceNode(nodes as Node<ServiceData>[]),
      );
    },
    [dispatch],
  );

  const handleNodesChange = (changes: NodeChange<Node<ServiceData>>[]) => {
    dispatch(onChatQnAGraphNodesChange(changes));
  };

  const fitViewOptions: FitViewOptions = {
    padding: nodes.length > 9 ? 0.25 : 0.5,
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
      deleteKeyCode={null}
    >
      <Controls showInteractive={false} fitViewOptions={fitViewOptions} />
    </ReactFlow>
  );
};

export default ChatQnAGraph;
