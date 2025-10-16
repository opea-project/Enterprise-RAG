// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useColorScheme } from "@intel-enterprise-rag-ui/components";
import {
  ConnectionLineType,
  Controls,
  type DefaultEdgeOptions,
  FitViewOptions,
  MarkerType,
  Node,
  NodeChange,
  NodeTypes,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import debounce from "lodash.debounce";
import { useCallback, useEffect, useMemo } from "react";

import ServiceNode from "@/features/admin-panel/control-plane/components/ServiceNode/ServiceNode";
import {
  chatQnAGraphEdgesSelector,
  chatQnAGraphNodesSelector,
  onChatQnAGraphConnect,
  onChatQnAGraphEdgesChange,
  onChatQnAGraphNodesChange,
  setChatQnAGraphSelectedServiceNode,
} from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { ServiceData } from "@/features/admin-panel/control-plane/types";
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

const ChatQnAGraphFlow = () => {
  const dispatch = useAppDispatch();
  const nodes = useAppSelector(chatQnAGraphNodesSelector);
  const edges = useAppSelector(chatQnAGraphEdgesSelector);

  const { colorScheme } = useColorScheme();
  const reactFlowInstance = useReactFlow();

  const handleSelectionChange = useCallback(
    ({ nodes }: { nodes: Node[] }) => {
      dispatch(
        setChatQnAGraphSelectedServiceNode(nodes as Node<ServiceData>[]),
      );
    },
    [dispatch],
  );

  const handleNodesChange = (changes: NodeChange<Node<ServiceData>>[]) => {
    dispatch(onChatQnAGraphNodesChange(changes));
  };

  const fitViewOptions: FitViewOptions = useMemo(
    () => ({
      padding: nodes.length > 9 ? 0.25 : 0.5,
    }),
    [nodes.length],
  );

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
      colorMode={colorScheme}
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
      onNodesChange={handleNodesChange}
      onEdgesChange={onChatQnAGraphEdgesChange}
      onConnect={onChatQnAGraphConnect}
      onSelectionChange={handleSelectionChange}
      fitView
    >
      <Controls showInteractive={false} fitViewOptions={fitViewOptions} />
    </ReactFlow>
  );
};

// Wrapping ChatQnAGraphFlow in ReactFlowProvider must be done outside of the component
const ChatQnAGraph = () => (
  <ReactFlowProvider>
    <ChatQnAGraphFlow />
  </ReactFlowProvider>
);

export default ChatQnAGraph;
