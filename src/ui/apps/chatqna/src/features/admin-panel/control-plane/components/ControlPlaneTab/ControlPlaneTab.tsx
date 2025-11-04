// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useColorScheme } from "@intel-enterprise-rag-ui/components";
import {
  ControlPlanePanel,
  PipelineGraph,
} from "@intel-enterprise-rag-ui/control-plane";
import { FitViewOptions, Node, NodeChange } from "@xyflow/react";
import { useCallback, useMemo } from "react";

import { useGetServicesDataQuery } from "@/features/admin-panel/control-plane/api";
import {
  chatQnAGraphEdgesSelector,
  chatQnAGraphIsLoadingSelector,
  chatQnAGraphIsRenderableSelector,
  chatQnAGraphNodesSelector,
  onChatQnAGraphConnect,
  onChatQnAGraphEdgesChange,
  onChatQnAGraphNodesChange,
  setChatQnAGraphSelectedServiceNode,
} from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { ServiceData } from "@/features/admin-panel/control-plane/types";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const ControlPlaneTab = () => {
  useGetServicesDataQuery();

  const isLoading = useAppSelector(chatQnAGraphIsLoadingSelector);
  const isRenderable = useAppSelector(chatQnAGraphIsRenderableSelector);

  return (
    <ControlPlanePanel
      isLoading={isLoading}
      isRenderable={isRenderable}
      Graph={ChatQnAGraph}
    />
  );
};

const ChatQnAGraph = () => {
  const dispatch = useAppDispatch();
  const nodes = useAppSelector(chatQnAGraphNodesSelector);
  const edges = useAppSelector(chatQnAGraphEdgesSelector);

  const { colorScheme: colorMode } = useColorScheme();

  const handleSelectionChange = useCallback(
    ({ nodes }: { nodes: Node<Record<string, unknown>>[] }) => {
      dispatch(
        setChatQnAGraphSelectedServiceNode(nodes as Node<ServiceData>[]),
      );
    },
    [dispatch],
  );

  const handleNodesChange = (
    changes: NodeChange<Node<Record<string, unknown>>>[],
  ) => {
    dispatch(
      onChatQnAGraphNodesChange(changes as NodeChange<Node<ServiceData>>[]),
    );
  };

  const fitViewOptions: FitViewOptions = useMemo(
    () => ({
      padding: nodes.length > 9 ? 0.25 : 0.5,
    }),
    [nodes.length],
  );

  return (
    <PipelineGraph
      nodes={nodes}
      edges={edges}
      fitViewOptions={fitViewOptions}
      onNodesChange={handleNodesChange}
      onEdgesChange={onChatQnAGraphEdgesChange}
      onSelectionChange={handleSelectionChange}
      onConnect={onChatQnAGraphConnect}
      colorMode={colorMode}
    />
  );
};

export default ControlPlaneTab;
